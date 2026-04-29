"""
Entity Memory: structured per-institution / per-counterparty knowledge store.

Tracks known quirks, failure patterns, and resolution strategies for
specific financial institutions (banks, processors, clearinghouses) so the
agent can inject institution-aware context when working on related tasks.

Storage: memory/entities.json  (one JSON array of EntityProfile objects)

Public API
──────────
  upsert_entity(profile)               — add or update an EntityProfile
  get_entity(entity_id)                — retrieve by ID
  search_entities(query)               — keyword/semantic search
  record_interaction(entity_id, ...)   — log a task outcome for an entity
  entity_context_for_task(task)        — formatted block for prompt injection
"""

import json
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

ENTITY_STORE = os.path.join("memory", "entities.json")
os.makedirs("memory", exist_ok=True)


# ─────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────

@dataclass
class EntityProfile:
    entity_id: str
    name: str
    entity_type: str                          # bank | processor | clearinghouse | counterparty
    rail_preferences: list = field(default_factory=list)   # e.g. ["swift_mx", "ach"]
    known_quirks: list = field(default_factory=list)        # free-text observations
    failure_patterns: list = field(default_factory=list)    # failure_type strings
    resolution_strategies: dict = field(default_factory=dict)  # failure_type -> strategy text
    interaction_count: int = 0
    raised_warnings: int = 0                  # times compliance WARN was triggered
    last_seen: str = ""                       # ISO timestamp of last interaction
    notes: str = ""                           # freeform notes

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "EntityProfile":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in known})


# ─────────────────────────────────────────────────────────────
# Persistence
# ─────────────────────────────────────────────────────────────

def _load_store() -> list[dict]:
    if os.path.exists(ENTITY_STORE):
        try:
            return json.load(open(ENTITY_STORE))
        except Exception:
            pass
    return []


def _save_store(profiles: list[dict]):
    with open(ENTITY_STORE, "w") as f:
        json.dump(profiles, f, indent=2)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────────────────────

def upsert_entity(profile: EntityProfile):
    """Add a new entity or replace an existing one by entity_id."""
    store = _load_store()
    store = [p for p in store if p.get("entity_id") != profile.entity_id]
    store.append(profile.to_dict())
    _save_store(store)


def get_entity(entity_id: str) -> Optional[EntityProfile]:
    """Return the EntityProfile for entity_id, or None if not found."""
    for p in _load_store():
        if p.get("entity_id") == entity_id:
            return EntityProfile.from_dict(p)
    return None


def list_entities() -> list[EntityProfile]:
    return [EntityProfile.from_dict(p) for p in _load_store()]


# ─────────────────────────────────────────────────────────────
# Interaction recording
# ─────────────────────────────────────────────────────────────

def record_interaction(
    entity_id: str,
    failure_type: Optional[str] = None,
    quirk: Optional[str] = None,
    compliance_warn: bool = False,
):
    """
    Record an interaction with an entity.
    Creates a minimal profile if the entity is unknown.
    """
    profile = get_entity(entity_id) or EntityProfile(
        entity_id=entity_id,
        name=entity_id,
        entity_type="unknown",
    )
    profile.interaction_count += 1
    profile.last_seen = _now_iso()

    if failure_type and failure_type not in profile.failure_patterns:
        profile.failure_patterns.append(failure_type)

    if quirk and quirk not in profile.known_quirks:
        profile.known_quirks.append(quirk)

    if compliance_warn:
        profile.raised_warnings += 1

    upsert_entity(profile)


# ─────────────────────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────────────────────

_embed_model = None


def _get_embed_model():
    global _embed_model
    if _embed_model is False:
        return None
    if _embed_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception:
            _embed_model = False
    return _embed_model if _embed_model is not False else None


def _cosine(a, b) -> float:
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _profile_text(p: EntityProfile) -> str:
    parts = [p.name, p.entity_type] + p.rail_preferences + p.known_quirks + p.failure_patterns
    return " ".join(str(x) for x in parts if x)


def search_entities(query: str, k: int = 3) -> list[EntityProfile]:
    """Return up to k EntityProfiles most relevant to a query."""
    profiles = list_entities()
    if not profiles:
        return []

    model = _get_embed_model()
    if model is not None:
        q_vec = model.encode(query).tolist()
        scored = []
        for p in profiles:
            p_vec = model.encode(_profile_text(p)).tolist()
            scored.append((_cosine(q_vec, p_vec), p))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for s, p in scored[:k] if s > 0.2]

    # Keyword fallback
    q_words = set(re.findall(r"\w+", query.lower()))
    scored = []
    for p in profiles:
        p_words = set(re.findall(r"\w+", _profile_text(p).lower()))
        scored.append((len(q_words & p_words), p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for s, p in scored[:k] if s > 0]


# ─────────────────────────────────────────────────────────────
# Prompt injection helper
# ─────────────────────────────────────────────────────────────

def entity_context_for_task(task: str, k: int = 2) -> str:
    """Return a formatted entity-memory block for system prompt injection."""
    matches = search_entities(task, k=k)
    if not matches:
        return ""
    lines = ["Entity memory (known institution quirks):"]
    for p in matches:
        lines.append(f"\n  {p.name} ({p.entity_type})")
        if p.rail_preferences:
            lines.append(f"    Rail preferences: {', '.join(p.rail_preferences)}")
        if p.known_quirks:
            lines.append(f"    Known quirks: {'; '.join(p.known_quirks)}")
        if p.failure_patterns:
            lines.append(f"    Past failure types: {', '.join(p.failure_patterns)}")
        if p.resolution_strategies:
            for ft, strategy in p.resolution_strategies.items():
                lines.append(f"    Resolution for {ft}: {strategy}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    # Smoke test
    p = EntityProfile(
        entity_id="test_bank_001",
        name="Test Bank",
        entity_type="bank",
        rail_preferences=["swift_mx", "ach"],
        known_quirks=["requires UETR in all pacs.008 messages"],
        failure_patterns=["missing_context"],
        resolution_strategies={"missing_context": "retrieve pacs.008 namespace docs"},
    )
    upsert_entity(p)
    retrieved = get_entity("test_bank_001")
    assert retrieved is not None, "expected to retrieve entity"
    assert retrieved.name == "Test Bank"
    record_interaction("test_bank_001", failure_type="hallucination", compliance_warn=True)
    updated = get_entity("test_bank_001")
    assert updated.interaction_count == 1
    assert updated.raised_warnings == 1
    assert "hallucination" in updated.failure_patterns
    ctx = entity_context_for_task("pacs.008 routing for Test Bank", k=1)
    assert "Test Bank" in ctx, f"expected entity in context: {ctx}"
    # Clean up
    store = _load_store()
    _save_store([p for p in store if p.get("entity_id") != "test_bank_001"])
    print("TEST PASSED")
