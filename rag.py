"""
RAG (Retrieval-Augmented Generation) layer for the payment agent.

Maintains a small corpus of seeded financial specification documents and
retrieves relevant chunks for any given task.

Embedding model (sentence-transformers/all-MiniLM-L6-v2) is used when
available; keyword-overlap scoring is the fallback.

Public API
──────────
  seed_documents()              — idempotent; write built-in docs to store
  add_document(id, title, text) — add/replace a document
  retrieve(query, k=3)          — return top-k relevant chunks
  rag_context_for_task(task)    — formatted block ready for system prompt injection
"""

import json
import os
import re

RAG_DIR = "rag"
RAG_STORE = os.path.join(RAG_DIR, "documents.json")

os.makedirs(RAG_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Seeded financial specification documents
# ─────────────────────────────────────────────────────────────

_SEEDED_DOCS = [
    {
        "id": "iso20022_overview",
        "title": "ISO 20022 Message Standard Overview",
        "content": (
            "ISO 20022 is the global financial messaging standard for electronic data interchange "
            "between financial institutions. Key message families:\n"
            "- pacs (Payments Clearing and Settlement): pacs.008 FI-to-FI credit transfer, "
            "pacs.009 financial institution credit transfer, pacs.002 payment status report\n"
            "- camt (Cash Management): camt.053 bank-to-customer statement, camt.054 debit/credit "
            "notification\n"
            "- pain (Payment Initiation): pain.001 customer credit transfer initiation, "
            "pain.002 customer payment status report\n"
            "MX messages use XML with strict namespace declarations. Each message has a Business "
            "Application Header (BAH) and a Document element. The namespace URI encodes the message "
            "type and version, e.g. urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08."
        ),
    },
    {
        "id": "nacha_ach_format",
        "title": "NACHA ACH File Format",
        "content": (
            "NACHA governs the ACH network in the US. ACH files use fixed-width 94-character records.\n"
            "Record types:\n"
            "- Type 1: File Header — routing transit number, file creation date\n"
            "- Type 5: Batch Header — company name, company ID, SEC code (PPD/CCD/CTX/WEB), "
            "effective date\n"
            "- Type 6: Entry Detail — transaction code, routing+account, amount (10-digit "
            "zero-padded cents), individual name, trace number\n"
            "- Type 8: Batch Control — entry count, debit/credit totals\n"
            "- Type 9: File Control — batch count, block count, entry count\n"
            "Routing numbers: 9 digits. ABA checksum: "
            "(3*d[0]+7*d[1]+d[2]+3*d[3]+7*d[4]+d[5]+3*d[6]+7*d[7]+d[8]) mod 10 == 0.\n"
            "Transaction codes: 22=checking credit, 27=checking debit, "
            "32=savings credit, 37=savings debit."
        ),
    },
    {
        "id": "swift_mx_migration",
        "title": "SWIFT MX Migration Timeline",
        "content": (
            "SWIFT is migrating from MT (message text) to MX (ISO 20022 XML) format.\n"
            "Key dates:\n"
            "- November 2022: coexistence period began\n"
            "- November 2025: MT to MX migration deadline for correspondent banking\n"
            "- November 2026: Hybrid address format mandatory — TwnNm and Ctry must be structured "
            "fields; max 2 unstructured AdrLine elements allowed\n"
            "The pacs.008 replaces MT103. pacs.009 replaces MT202. camt.053 replaces MT940/MT942.\n"
            "During coexistence the SWIFT translation service converts between MT and MX."
        ),
    },
    {
        "id": "iso20022_address",
        "title": "ISO 20022 Hybrid Address Format (PostalAddress24)",
        "content": (
            "ISO 20022 postal addresses (PostalAddress24) mix structured and unstructured fields.\n"
            "Mandatory from November 2026:\n"
            "- TwnNm (town name): required, max 35 chars\n"
            "- Ctry (country): required, ISO 3166-1 alpha-2 (2 uppercase letters)\n"
            "Optional structured: StrtNm, BldgNb, PstCd\n"
            "Optional unstructured: AdrLine[0..2] — max 70 chars each, max 2 lines\n"
            "Hybrid = TwnNm + Ctry + AdrLine. Full structured = all structured fields, no AdrLine."
        ),
    },
    {
        "id": "reconciliation_patterns",
        "title": "Cross-Rail Payment Reconciliation Patterns",
        "content": (
            "Reconciliation matches transactions across payment rails.\n"
            "Key patterns:\n"
            "- Reference matching: end-to-end ID, UETR, or instruction ID\n"
            "- Amount tolerance: typical 0.01% for FX rounding\n"
            "- Status flow: PDNG → ACCP → ACSC → RJCT\n"
            "- Exception handling: surface unmatched, flag partial, detect duplicates\n"
            "UETR: 36-char UUID used in SWIFT MX for end-to-end tracking.\n"
            "Settlement cutoffs: FedNow 24/7, ACH next-day/same-day windows."
        ),
    },
    {
        "id": "compliance_pii",
        "title": "Payment Data Compliance and PII Requirements",
        "content": (
            "Payment messages contain sensitive PII subject to regulatory requirements.\n"
            "- GDPR Article 4: name, IBAN, account number are personal data\n"
            "- FinCEN/BSA: customer due diligence records retained 5 years\n"
            "- PCI DSS: PAN must be masked to last 4 digits\n"
            "- Audit trail: every access to account number, IBAN, or amount must be logged\n"
            "Masking rules: account numbers → last 4 visible (****1234); IBANs → country + last 4.\n"
            "AML: transactions >$10 000 trigger CTR filing; structuring patterns flagged."
        ),
    },
    {
        "id": "ledger_entry_fields",
        "title": "Ledger Entry Standard Fields",
        "content": (
            "A LedgerEntry represents one transaction in an internal ledger.\n"
            "Standard fields:\n"
            "- entry_id: unique identifier (payment end-to-end ID or reference)\n"
            "- amount: Decimal; positive = credit, negative = debit\n"
            "- currency: ISO 4217 3-letter code (USD, EUR, GBP)\n"
            "- counterparty: name or BIC of the other party\n"
            "- reference: matching key (UETR, end-to-end ID)\n"
            "- rail: iso20022 | ach | fedwire | sepa | internal\n"
            "- value_date: when funds are available\n"
            "- booking_date: when transaction is booked in the ledger"
        ),
    },
]


# ─────────────────────────────────────────────────────────────
# Document store
# ─────────────────────────────────────────────────────────────

def _load_store() -> list[dict]:
    if os.path.exists(RAG_STORE):
        try:
            return json.load(open(RAG_STORE))
        except Exception:
            pass
    return []


def _save_store(docs: list[dict]):
    with open(RAG_STORE, "w") as f:
        json.dump(docs, f, indent=2)


def seed_documents() -> int:
    """Write built-in documents to the store (idempotent). Returns count added."""
    existing = _load_store()
    existing_ids = {d["id"] for d in existing}
    added = 0
    for doc in _SEEDED_DOCS:
        if doc["id"] not in existing_ids:
            existing.append(doc)
            added += 1
    if added:
        _save_store(existing)
    return added


def add_document(doc_id: str, title: str, content: str):
    """Add or replace a document in the RAG store."""
    docs = _load_store()
    docs = [d for d in docs if d["id"] != doc_id]
    docs.append({"id": doc_id, "title": title, "content": content})
    _save_store(docs)


# ─────────────────────────────────────────────────────────────
# Chunking
# ─────────────────────────────────────────────────────────────

def _chunk_doc(doc: dict, chunk_size: int = 400, overlap: int = 80) -> list[dict]:
    text = doc["content"]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append({
            "doc_id": doc["id"],
            "title": doc["title"],
            "text": text[start:end],
        })
        start += chunk_size - overlap
    return chunks


def _all_chunks() -> list[dict]:
    chunks = []
    for doc in _load_store():
        chunks.extend(_chunk_doc(doc))
    return chunks


# ─────────────────────────────────────────────────────────────
# Embedding helpers (lazy-loaded)
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


# ─────────────────────────────────────────────────────────────
# Retrieval
# ─────────────────────────────────────────────────────────────

def retrieve(query: str, k: int = 3) -> list[dict]:
    """Return top-k most relevant document chunks for a query."""
    chunks = _all_chunks()
    if not chunks:
        return []

    model = _get_embed_model()
    if model is not None:
        q_vec = model.encode(query).tolist()
        scored = []
        for chunk in chunks:
            c_vec = model.encode(chunk["text"]).tolist()
            scored.append((_cosine(q_vec, c_vec), chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for s, c in scored[:k] if s > 0.15]

    # Keyword fallback
    q_words = set(re.findall(r"\w+", query.lower()))
    scored = []
    for chunk in chunks:
        c_words = set(re.findall(r"\w+", chunk["text"].lower()))
        scored.append((len(q_words & c_words), chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for s, c in scored[:k] if s > 0]


def rag_context_for_task(task: str, k: int = 3) -> str:
    """Return a formatted RAG context block ready for system prompt injection."""
    seed_documents()
    chunks = retrieve(task, k=k)
    if not chunks:
        return ""
    lines = ["Financial specification context (from RAG store):"]
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"\n[{i}] {chunk['title']}")
        lines.append(chunk["text"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    seed_documents()
    results = retrieve("ABA routing number checksum NACHA", k=2)
    assert results, "expected at least one result"
    print(f"Retrieved {len(results)} chunk(s)")
    for r in results:
        print(f"  [{r['doc_id']}] {r['text'][:80].strip()}...")
    ctx = rag_context_for_task("validate ISO 20022 pacs.008 XML parsing")
    assert "ISO 20022" in ctx or "pacs" in ctx, "expected payment context in output"
    print("TEST PASSED")
