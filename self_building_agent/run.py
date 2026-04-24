import os, json, re, yaml, subprocess, tempfile, ast, hashlib, shutil, sys, time
from datetime import datetime, timezone
from collections import deque

PYTHON_BIN = sys.executable  # use the same Python that's running the agent
from google import genai
from google.genai import types as genai_types

# Optional addons — imported lazily so existing tests keep working if a module
# hasn't been created yet.
def _try_import(module):
    try:
        return __import__(module)
    except ImportError:
        return None

PY_SKILLS_DIR = "skills_py"
PY_SKILLS_ARCHIVE = "skills_py/archive"
EPISODES_FILE = "memory/episodes.jsonl"
LOG_FILE = "logs/log.jsonl"

for _d in (PY_SKILLS_DIR, PY_SKILLS_ARCHIVE, "memory", "logs", "skills"):
    os.makedirs(_d, exist_ok=True)

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


class TokenBudget:
    """Tracks estimated Gemini API cost and warns before hitting budget."""
    _PRICING = {  # USD per million tokens (pay-as-you-go; free tier has no cost)
        "gemini-2.5-flash":      {"input": 0.15, "output": 0.60},
        "gemini-2.0-flash":      {"input": 0.10, "output": 0.40},
        "gemini-2.0-flash-lite": {"input": 0.075, "output": 0.30},
        "gemini-1.5-flash":      {"input": 0.075, "output": 0.30},
        "gemini-1.5-pro":        {"input": 1.25, "output": 5.00},
        "gemini-2.5-pro":        {"input": 1.25, "output": 10.00},
    }
    INPUT_EST  = 2000   # tokens per call (conservative)
    OUTPUT_EST = 500

    def __init__(self, model: str, budget_usd: float = float(os.environ.get("GEMINI_BUDGET_USD", "2.00"))):
        p = self._PRICING.get(model, {"input": 0.10, "output": 0.40})
        self.budget_usd = budget_usd
        self.cost_per_call = (self.INPUT_EST * p["input"] + self.OUTPUT_EST * p["output"]) / 1_000_000
        self.calls = 0
        self.estimated_cost = 0.0

    def can_run(self) -> bool:
        return self.estimated_cost + self.cost_per_call < self.budget_usd

    def record_call(self):
        self.calls += 1
        self.estimated_cost += self.cost_per_call

    def status(self) -> str:
        return f"~${self.estimated_cost:.4f}/${self.budget_usd:.2f} ({self.calls} calls)"

    def calls_remaining(self) -> int:
        return max(0, int((self.budget_usd - self.estimated_cost) / self.cost_per_call))


budget = TokenBudget(MODEL)


def _llm(messages, max_tokens=2000):
    """Thin wrapper: extracts system role, converts to Gemini format, calls API."""
    if not budget.can_run():
        print(f"  [BUDGET] Soft limit reached — {budget.status()}. Set GEMINI_BUDGET_USD to increase.")
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    user_messages = [m for m in messages if m["role"] != "system"]

    system_instruction = "\n\n".join(system_parts) if system_parts else None

    # Build Gemini content list (role "assistant" → "model")
    if len(user_messages) == 1:
        contents = user_messages[0]["content"]
    else:
        contents = [
            genai_types.Content(
                role="model" if m["role"] == "assistant" else "user",
                parts=[genai_types.Part(text=m["content"])]
            )
            for m in user_messages
        ]

    cfg = genai_types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        system_instruction=system_instruction,
    )
    for attempt in range(4):
        try:
            r = client.models.generate_content(model=MODEL, contents=contents, config=cfg)
            budget.record_call()
            return r.text
        except Exception as e:
            msg = str(e)
            if "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
                wait = 15 * (2 ** attempt)
                print(f"  [retry] 503 overloaded, waiting {wait}s (attempt {attempt+1}/4)...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Gemini API still unavailable after 4 attempts")

# Optional embedding model for semantic skill selection fallback.
# Loaded lazily so the agent still runs if sentence-transformers isn't installed.
_embed_model = None
_skill_embed_cache = {}  # name -> (text_hash, vector)

def _get_embed_model():
    global _embed_model
    if _embed_model is False:
        return None
    if _embed_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception as e:
            print(f"  [embedding model unavailable: {e}]")
            _embed_model = False
            return None
    return _embed_model

def _cosine(a, b):
    import math
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    return dot / (na * nb) if na and nb else 0.0

def dynamic_top_k(skills: list, relevance_scores: list = None) -> int:
    """Compute an adaptive top_k based on skill library size and score distribution."""
    n = len(skills)
    if n == 0:
        return 0
    elif n <= 5:
        k = min(2, n)
    elif n <= 15:
        k = 3
    elif n <= 30:
        k = 4
    else:
        k = 5
    # Boost if average relevance is high
    if relevance_scores and len(relevance_scores) >= 3:
        mean = sum(relevance_scores) / len(relevance_scores)
        if mean > 0.6:
            k = min(k + 1, n)
    return k


def embed_rank_skills(task, skills, top_k=3):
    model = _get_embed_model()
    if model is None or not skills:
        return []
    task_vec = model.encode(task).tolist()
    scored = []
    for s in skills:
        name = s["metadata"]["name"]
        text = f"{name}. {s['metadata'].get('trigger','')}. tags: {', '.join(s['metadata'].get('tags', []))}"
        h = hash(text)
        cached = _skill_embed_cache.get(name)
        if cached and cached[0] == h:
            vec = cached[1]
        else:
            vec = model.encode(text).tolist()
            _skill_embed_cache[name] = (h, vec)
        scored.append((_cosine(task_vec, vec), s))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for score, s in scored[:top_k] if score > 0.2]

SKILL_CREATION_INSTRUCTIONS = """After completing a task, evaluate whether it warrants a new skill.
Do NOT create a skill that already exists. If a relevant skill is already listed, use it instead.

Only write a skill if ALL of these are true:
- The situation will recur in this specific environment
- The approach was non-obvious and not general programming knowledge
- Something specific to this user/codebase made it different from standard practice

If and ONLY if the task meets all criteria above, use this format:
---NEW SKILL---
filename: skill_name.md
name: skill_name
tags: [tag1, tag2, tag3]
trigger: one sentence describing when this skill should be used
type: pattern
---
# Skill Title
## Purpose
Describe the purpose here.
## When to use
Describe when to use this skill.
## How to use
Describe how to use this skill with concrete steps.
---END SKILL---

Write ACTUAL content. Do NOT use placeholders like [content].
If no skill is needed, just complete the task and stop."""


# ---------------------------------------------------------------------------
# Skill parsing & persistence
# ---------------------------------------------------------------------------

def parse_skill(filepath):
    raw = open(filepath).read()
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        metadata = yaml.safe_load(parts[1]) or {}
        content = parts[2].strip() if len(parts) > 2 else ""
    else:
        metadata = {}
        content = raw

    metadata.setdefault("name", os.path.basename(filepath).replace(".md", ""))
    metadata.setdefault("tags", [])
    metadata.setdefault("trigger", "")
    metadata.setdefault("type", "pattern")
    metadata.setdefault("version", 1)
    metadata.setdefault("success_count", 0)
    metadata.setdefault("fail_count", 0)

    return {"metadata": metadata, "content": content, "filepath": filepath}


def load_all_skills():
    skills = []
    for f in sorted(os.listdir("skills")):
        if f.endswith(".md"):
            skill = parse_skill(f"skills/{f}")
            # Auto-retire: skip skills that consistently fail
            m = skill["metadata"]
            if m["fail_count"] > 5 and m["success_count"] == 0:
                continue
            skills.append(skill)
    return skills


def save_skill(skill):
    frontmatter = yaml.dump(skill["metadata"], default_flow_style=False, sort_keys=False)
    with open(skill["filepath"], "w") as f:
        f.write(f"---\n{frontmatter}---\n{skill['content']}")


# ---------------------------------------------------------------------------
# Skill selection
# ---------------------------------------------------------------------------

def select_skills(task, all_skills):
    if not all_skills:
        return [], 0

    # Stage 1: loose keyword pre-filter (substring matching, both directions)
    task_lower = task.lower()
    task_words = set(re.findall(r'\w+', task_lower))
    candidates = []
    for s in all_skills:
        m = s["metadata"]
        matched = False
        # Substring match: any tag appearing in task text, or task word appearing in any tag
        for t in m.get("tags", []):
            tl = t.lower()
            if tl in task_lower or any(tl in w or w in tl for w in task_words if len(w) > 2):
                matched = True
                break
        # Substring match against trigger
        if not matched:
            trigger = m.get("trigger", "").lower()
            if trigger and any(w in trigger for w in task_words if len(w) > 3):
                matched = True
        # High-success skills always candidate
        if not matched and m.get("success_count", 0) > 3:
            matched = True
        if matched:
            candidates.append(s)

    # Embedding-based fallback: surface top semantic matches regardless of keyword overlap
    embed_matches = embed_rank_skills(task, all_skills, top_k=dynamic_top_k(all_skills))
    for s in embed_matches:
        if s not in candidates:
            candidates.append(s)

    # Final fallback: if still nothing, send all skills to LLM ranker (cheap; only ~6 of them)
    if not candidates:
        candidates = list(all_skills)

    considered = len(candidates)

    # Stage 2: LLM-based selection
    skill_descriptions = "\n".join(
        f"- {s['metadata']['name']}: {s['metadata'].get('trigger', 'no trigger defined')}"
        for s in candidates
    )
    prompt = f"""Given this task: "{task}"

Which of these skills are relevant? Return ONLY a JSON list of skill names, e.g. ["skill_a"]. If none are relevant, return [].

Available skills:
{skill_descriptions}"""

    try:
        raw = _llm([{"role": "user", "content": prompt}], max_tokens=200).strip()
        # Extract JSON array from response (LLM may wrap it in text)
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        selected_names = json.loads(match.group()) if match else []
    except Exception:
        selected_names = []

    return [s for s in candidates if s["metadata"]["name"] in selected_names], considered


# ---------------------------------------------------------------------------
# Code execution
# ---------------------------------------------------------------------------

def extract_code_block(response_text):
    if "---EXECUTE---" not in response_text:
        return None
    block = response_text.split("---EXECUTE---")[1].split("---END EXECUTE---")[0]
    # Strip markdown code fences
    block = re.sub(r'```\w*\n?', '', block).strip()
    return block


def execute_code(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        try:
            result = subprocess.run(
                [PYTHON_BIN, f.name],
                capture_output=True, text=True, timeout=30
            )
            output = result.stdout
            if result.stderr:
                output += "\nSTDERR:\n" + result.stderr
            return output[:2000]
        except subprocess.TimeoutExpired:
            return "ERROR: Execution timed out after 30 seconds"
        finally:
            os.unlink(f.name)


# ---------------------------------------------------------------------------
# Task execution (multi-turn with code execution)
# ---------------------------------------------------------------------------

def run_task(task, selected_skills, all_skills=None, episodes=None):
    skill_context = ""
    for s in selected_skills:
        skill_context += f"\n### Skill: {s['metadata']['name']} (type: {s['metadata']['type']})\n{s['content']}\n"

    # Always advertise the full skill library by name+trigger so the model can reference it.
    skill_index = ""
    if all_skills:
        skill_index = "\n".join(
            f"- {s['metadata']['name']}: {s['metadata'].get('trigger','(no trigger)')}"
            for s in all_skills
        )

    episode_block = ""
    if episodes:
        episode_block = "Similar past tasks (episodic memory):\n" + "\n".join(
            f"- [{e.get('outcome','?')}] {e.get('task','')[:120]} (skills: {', '.join(e.get('skills_used', []) or [])})"
            for e in episodes
        ) + "\n"

    # RAG context — financial specification documents
    rag_block = ""
    try:
        from rag import rag_context_for_task
        rag_block = rag_context_for_task(task, k=3)
    except ImportError:
        pass

    # Entity memory — known institution quirks
    entity_block = ""
    try:
        from entity_memory import entity_context_for_task
        entity_block = entity_context_for_task(task, k=2)
    except ImportError:
        pass

    # MCP tool manifest
    mcp_block = ""
    try:
        from mcp_client import tool_manifest_for_prompt
        mcp_block = tool_manifest_for_prompt()
    except ImportError:
        pass

    system = f"""You are a self-building agent. You solve programming tasks, execute code, and grow your own skill library.

{episode_block}{rag_block}{entity_block}{mcp_block}
Available skills (you may reference any of these by name when relevant):
{skill_index or "(none yet)"}

{"Relevant skills loaded for this task:" + skill_context if skill_context else "No specific skills were pre-loaded for this task."}

==================================================================
RESPONSE FORMAT — your response MUST follow this structure.
Do not omit these blocks. Even if you are uncertain, attempt them.
==================================================================

1. Brief reasoning (1-3 sentences).

2. If the task requires running code, you MUST wrap an executable Python snippet in EXECUTE markers. Example:

---EXECUTE---
```python
def reverse_string(s):
    return s[::-1]
print(reverse_string("hello"))
```
---END EXECUTE---

3a. MANDATORY: for every coding task you MUST emit a ---PY SKILL--- block containing a
self-contained Python function with a unit test. Do not just explain the solution — write
the actual function. The test block MUST use plain assert statements (no pytest/unittest)
and MUST end with exactly: print("TEST PASSED")
Runnable as: python skill_file.py
Example correct test format:
if __name__ == "__main__":
    result = my_function(test_input)
    assert result == expected_output, f"Got {{result}}"
    print("TEST PASSED")

For payment-domain skills, include these header fields at the top of the function body (as comments, before the def):
# protocol: one of iso20022|ach|fedwire|sepa|internal|general
# rail: one of swift_mx|fednow|rtp|nacha|sepa_ct|on_chain|general
# audit_required: true if the skill reads or writes party PII or financial amounts
Example:

---PY SKILL---
def reverse_string(s):
    'Return the reverse of a string.'
    return s[::-1]

if __name__ == "__main__":
    assert reverse_string("hello") == "olleh"
    assert reverse_string("") == ""
    print("TEST PASSED")
---END PY SKILL---

3b. Or, if your insight is more conceptual than executable, emit a NEW SKILL block instead. Example:

---NEW SKILL---
filename: example_skill.md
name: example_skill
tags: [example, demo]
trigger: when doing the example thing
type: pattern
---
# Example Skill
## Purpose
Real content here, never placeholders.
## When to use
Concrete situations.
## How to use
Concrete steps.
---END SKILL---

4. After every task, ask yourself: "What follow-up task would make this agent more capable?"
   You MUST emit at least one NEW TASK block unless the task is purely terminal. Example:

---NEW TASK---
Write a unit test for the reverse_string function above
---END TASK---

Do not omit these blocks. Even if you are uncertain, attempt them.

{SKILL_CREATION_INSTRUCTIONS}
"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": task}
    ]

    max_iterations = 3
    execution_results = []
    reply = ""

    for i in range(max_iterations):
        reply = _llm(messages, max_tokens=8000)

        # MCP tool calls take priority over EXECUTE blocks
        try:
            from mcp_client import execute_tool_calls, register_agent_tools
            tool_results = execute_tool_calls(reply)
            register_agent_tools(reply)
        except ImportError:
            tool_results = []

        if tool_results:
            tool_summary = "\n".join(
                f"Tool '{r['call'].get('tool','?')}' result:\n{r['result'][:500]}"
                for r in tool_results
            )
            print(f"  [MCP tools executed: {[r['call'].get('tool') for r in tool_results]}]")
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": f"{tool_summary}\n\nContinue or finalize your response."})
            continue

        code = extract_code_block(reply)
        if code:
            result = execute_code(code)
            execution_results.append({"code": code, "result": result})
            print(f"  [Executed code, result: {result[:200]}...]")
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": f"Execution result:\n{result}\n\nContinue or finalize your response."})
        else:
            break

    return reply, execution_results


# ---------------------------------------------------------------------------
# Autonomous task generation
# ---------------------------------------------------------------------------

def extract_new_tasks(response_text):
    tasks = []
    if "---NEW TASK---" not in response_text:
        return tasks
    blocks = response_text.split("---NEW TASK---")[1:]
    for block in blocks:
        task_text = block.split("---END TASK---")[0].strip()
        if task_text and len(task_text) > 5:
            tasks.append(task_text)
    return tasks


# ---------------------------------------------------------------------------
# Skill creation from LLM response
# ---------------------------------------------------------------------------

def extract_and_save_skill(response_text):
    if "---NEW SKILL---" not in response_text:
        return None

    skill_block = response_text.split("---NEW SKILL---")[1]
    skill_block = skill_block.split("---END SKILL---")[0].strip()

    first_line = skill_block.split("\n")[0]
    filename = first_line.replace("filename:", "").strip()
    remaining = "\n".join(skill_block.split("\n")[1:]).strip()

    # Parse frontmatter from the skill block if present
    metadata = {}
    content = remaining
    if remaining.startswith("name:") or remaining.startswith("tags:"):
        # Metadata lines before the markdown content
        meta_lines = []
        body_lines = []
        in_meta = True
        for line in remaining.split("\n"):
            if in_meta and re.match(r'^(name|tags|trigger|type):', line):
                meta_lines.append(line)
            else:
                in_meta = False
                body_lines.append(line)
        if meta_lines:
            try:
                metadata = yaml.safe_load("\n".join(meta_lines)) or {}
            except yaml.YAMLError:
                pass
        content = "\n".join(body_lines).strip()

    # Also handle --- delimited frontmatter
    if remaining.startswith("---"):
        parts = remaining.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                pass
            content = parts[2].strip()

    # Skip placeholder content
    if not content or content.strip("[] \n") in ("content", "content as above", ""):
        print(f"  Skill '{filename}' has placeholder content, skipping.")
        return None

    # Skip duplicates: check filename AND content similarity against existing skills
    existing_skills = load_all_skills()
    existing_names = {os.path.basename(s["filepath"]) for s in existing_skills}
    if filename in existing_names:
        print(f"  Skill '{filename}' already exists (filename match), skipping.")
        return None

    def _normalize(text):
        return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', '', text.lower())).strip()

    new_norm = _normalize(content[:400])
    new_tags = set(t.lower() for t in metadata.get("tags", []))
    new_trigger = _normalize(metadata.get("trigger", ""))
    new_words = set(new_norm.split())

    for existing in existing_skills:
        em = existing["metadata"]
        # Trigger near-match
        if new_trigger and _normalize(em.get("trigger", "")) == new_trigger:
            print(f"  Skill '{filename}' duplicates '{em['name']}' (same trigger), skipping.")
            return None
        # Heavy tag overlap
        ex_tags = set(t.lower() for t in em.get("tags", []))
        if new_tags and ex_tags and len(new_tags & ex_tags) >= max(2, len(new_tags) // 2):
            # Confirm with body Jaccard similarity
            ex_words = set(_normalize(existing["content"][:400]).split())
            if new_words and ex_words:
                jaccard = len(new_words & ex_words) / len(new_words | ex_words)
                if jaccard > 0.5:
                    print(f"  Skill '{filename}' duplicates '{em['name']}' (jaccard={jaccard:.2f}), skipping.")
                    return None

    # Build full skill with frontmatter
    metadata.setdefault("name", filename.replace(".md", ""))
    metadata.setdefault("tags", [])
    metadata.setdefault("trigger", "")
    metadata.setdefault("type", "pattern")
    metadata.setdefault("version", 1)
    metadata.setdefault("success_count", 0)
    metadata.setdefault("fail_count", 0)

    skill = {"metadata": metadata, "content": content, "filepath": f"skills/{filename}"}
    save_skill(skill)
    return filename


# ---------------------------------------------------------------------------
# Feedback loop
# ---------------------------------------------------------------------------

def evaluate_skill_usage(task, response, exec_results, selected_skills):
    if not selected_skills:
        return

    skill_names = [s["metadata"]["name"] for s in selected_skills]
    exec_summary = ""
    if exec_results:
        exec_summary = f"\nCode was executed {len(exec_results)} time(s). Last result: {exec_results[-1]['result'][:500]}"

    prompt = f"""Task: "{task}"
Response summary: {response[:500]}
{exec_summary}

Skills used: {skill_names}

For each skill, did it meaningfully help complete this task?
Return ONLY JSON: {{"skill_name": true/false, ...}}"""

    try:
        raw = _llm([{"role": "user", "content": prompt}], max_tokens=200).strip()
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        verdicts = json.loads(match.group()) if match else {}
    except Exception:
        return

    for skill in selected_skills:
        name = skill["metadata"]["name"]
        if name in verdicts:
            if verdicts[name]:
                skill["metadata"]["success_count"] += 1
                print(f"  Skill '{name}' marked as helpful.")
            else:
                skill["metadata"]["fail_count"] += 1
                print(f"  Skill '{name}' marked as unhelpful.")
            save_skill(skill)

            # Queue a refinement task if skill is consistently failing
            m = skill["metadata"]
            if m["fail_count"] > 3 and m["fail_count"] > m["success_count"]:
                return f"Refine skill '{name}': it has {m['fail_count']} failures vs {m['success_count']} successes. Review and improve or remove it."
    return None


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_result(**fields):
    entry = {"timestamp": _now_iso()}
    entry.update(fields)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ===========================================================================
# PYTHON SKILL SYSTEM (skills_py/) — verified, executable, evolvable
# ===========================================================================

PY_SKILL_META_KEYS = ("skill", "version", "tags", "success_count", "fail_count",
                      "verified", "last_used", "decaying",
                      "protocol", "rail", "audit_required", "compliance_warn")

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def parse_py_skill(filepath):
    """Read a skills_py/*.py file and return {metadata, body, filepath}."""
    raw = open(filepath).read()
    metadata = {}
    body_lines = []
    in_header = True
    for line in raw.splitlines():
        if in_header and line.startswith("#") and ":" in line:
            key, _, val = line.lstrip("# ").partition(":")
            key = key.strip()
            val = val.strip()
            if key in PY_SKILL_META_KEYS:
                if key == "tags":
                    metadata[key] = [t.strip() for t in val.split(",") if t.strip()]
                elif key in ("version", "success_count", "fail_count"):
                    try:
                        metadata[key] = int(val)
                    except ValueError:
                        metadata[key] = 0
                elif key in ("verified", "decaying", "audit_required"):
                    metadata[key] = val.lower() == "true"
                else:
                    metadata[key] = val
                continue
        in_header = False
        body_lines.append(line)
    metadata.setdefault("skill", os.path.basename(filepath).replace(".py", ""))
    metadata.setdefault("version", 1)
    metadata.setdefault("tags", [])
    metadata.setdefault("success_count", 0)
    metadata.setdefault("fail_count", 0)
    metadata.setdefault("verified", False)
    metadata.setdefault("last_used", _now_iso())
    metadata.setdefault("decaying", False)
    return {"metadata": metadata, "body": "\n".join(body_lines).strip(), "filepath": filepath}

def serialize_py_skill(skill):
    m = skill["metadata"]
    header = [
        f"# skill: {m['skill']}",
        f"# version: {m['version']}",
        f"# tags: {', '.join(m.get('tags', []))}",
        f"# success_count: {m.get('success_count', 0)}",
        f"# fail_count: {m.get('fail_count', 0)}",
        f"# verified: {'true' if m.get('verified') else 'false'}",
        f"# last_used: {m.get('last_used', _now_iso())}",
        f"# decaying: {'true' if m.get('decaying') else 'false'}",
    ]
    for opt in ("protocol", "rail", "audit_required", "compliance_warn"):
        if m.get(opt) is not None:
            val = m[opt]
            if isinstance(val, bool):
                val = "true" if val else "false"
            header.append(f"# {opt}: {val}")
    header.append("")
    return "\n".join(header) + skill["body"].strip() + "\n"

def save_py_skill(skill):
    with open(skill["filepath"], "w") as f:
        f.write(serialize_py_skill(skill))
    # Maintain skills_py/index.json so dashboard can list files + metadata
    try:
        idx_files = sorted(f for f in os.listdir(PY_SKILLS_DIR) if f.endswith(".py"))
        idx_meta = []
        for fn in idx_files:
            try:
                s = parse_py_skill(f"{PY_SKILLS_DIR}/{fn}")
                m = s["metadata"]
                idx_meta.append({
                    "file": fn,
                    "skill": m.get("skill", fn),
                    "version": m.get("version", 1),
                    "tags": m.get("tags", []),
                    "verified": m.get("verified", False),
                    "protocol": m.get("protocol"),
                    "rail": m.get("rail"),
                    "audit_required": m.get("audit_required", False),
                    "compliance_warn": m.get("compliance_warn"),
                    "success_count": m.get("success_count", 0),
                    "fail_count": m.get("fail_count", 0),
                })
            except Exception:
                idx_meta.append({"file": fn})
        with open(f"{PY_SKILLS_DIR}/index.json", "w") as f:
            json.dump(idx_meta, f, indent=2)
    except Exception:
        pass

def load_py_skills():
    skills = []
    for f in sorted(os.listdir(PY_SKILLS_DIR)):
        if f.endswith(".py"):
            try:
                skills.append(parse_py_skill(f"{PY_SKILLS_DIR}/{f}"))
            except Exception as e:
                print(f"  [skipped {f}: {e}]")
    apply_decay(skills)
    return skills

def verify_py_skill(code, timeout=30):
    """AST-parse, then execute in subprocess. Returns (passed, output)."""
    try:
        ast.parse(code)
    except SyntaxError as e:
        print(f"  [verify] SYNTAX ERROR: {e}")
        return False, f"SYNTAX ERROR: {e}"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        result = subprocess.run(
            [PYTHON_BIN, path], capture_output=True, text=True, timeout=timeout
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        out = stdout + ("\nSTDERR:\n" + stderr if stderr else "")
        passed = result.returncode == 0 and "TEST PASSED" in stdout
        if not passed:
            reason = "no TEST PASSED in stdout" if result.returncode == 0 else f"exit {result.returncode}"
            print(f"  [verify] FAILED ({reason})")
            if stderr:
                print(f"  [verify] stderr: {stderr[:300]}")
            if stdout and "TEST PASSED" not in stdout:
                print(f"  [verify] stdout: {stdout[:200]}")
        return passed, out[:2000]
    except subprocess.TimeoutExpired:
        print(f"  [verify] TIMEOUT after {timeout}s")
        return False, f"TIMEOUT after {timeout}s"
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

def extract_py_skill_block(response_text):
    """Pull a ---PY SKILL--- block out of an LLM response."""
    if "---PY SKILL---" not in response_text:
        return None
    body = response_text.split("---PY SKILL---", 1)[1]
    body = body.split("---END PY SKILL---", 1)[0]
    # Strip code fences
    body = re.sub(r"^```\w*\s*", "", body.strip())
    body = re.sub(r"```\s*$", "", body).strip()
    return body or None

def _infer_skill_name(code):
    m = re.search(r"^def\s+(\w+)\s*\(", code, re.MULTILINE)
    return m.group(1) if m else f"skill_{hashlib.md5(code.encode()).hexdigest()[:8]}"

def _infer_tags(code, task):
    words = re.findall(r"\w+", (task or "").lower())
    stop = {"the", "a", "an", "for", "and", "to", "of", "that", "with", "in", "on", "is", "be"}
    return list(dict.fromkeys(w for w in words if len(w) > 3 and w not in stop))[:5]

def materialize_py_skill(code, task=""):
    """Verify code; if it passes ComplianceShield, persist as a new py skill. Returns (status, skill_or_msg)."""
    name = _infer_skill_name(code)
    filepath = f"{PY_SKILLS_DIR}/{name}.py"
    if os.path.exists(filepath):
        return "duplicate", name
    passed, output = verify_py_skill(code)
    if not passed:
        return "failed", output

    # Parse any payment-domain metadata out of the code header comments
    extra_meta = {}
    for line in code.splitlines():
        if not line.startswith("#"):
            break
        for key in ("protocol", "rail", "audit_required"):
            m = re.match(rf"#\s*{key}\s*:\s*(.+)", line)
            if m:
                val = m.group(1).strip()
                extra_meta[key] = val.lower() == "true" if key == "audit_required" else val

    metadata = {
        "skill": name, "version": 1, "tags": _infer_tags(code, task),
        "success_count": 0, "fail_count": 0,
        "verified": True, "last_used": _now_iso(), "decaying": False,
        **extra_meta,
    }

    # ComplianceShield check
    try:
        from compliance import check as shield_check, ShieldOutcome
        shield_result = shield_check(code, metadata)
        if shield_result.outcome == ShieldOutcome.BLOCK:
            log_result(
                task=task, response="", outcome="skill_blocked",
                skill_written=None, skill_verified=None, skill_verify_failed=True,
                skills_used=[], skills_considered=0, skill_composed=False,
                composed_from=[], skill_evolved=False, skill_version=None,
                code_executed=0, new_tasks_queued=[],
                failure_type="tool_misuse", recovery_attempted=False,
                recovery_succeeded=False,
                compliance_block=True, compliance_reason=shield_result.reason,
            )
            print(f"  ✗ ComplianceShield BLOCKED '{name}': {shield_result.reason}")
            return "blocked", shield_result.reason
        elif shield_result.outcome == ShieldOutcome.WARN:
            metadata["compliance_warn"] = shield_result.reason
            print(f"  ⚠ ComplianceShield WARN '{name}': {shield_result.reason}")
    except ImportError:
        pass  # compliance.py not available — skip shield

    # ValidationAgent: adversarial edge-case testing before final persist
    try:
        from validation_agent import run_validation
        val_passed, val_detail = run_validation(code, task)
        if not val_passed:
            print(f"  ✗ ValidationAgent FAILED '{name}': {val_detail[:200]}")
            log_result(
                task=task, response="", outcome="skill_validation_failed",
                skill_written=None, skill_verified=None, skill_verify_failed=True,
                skills_used=[], skills_considered=0, skill_composed=False,
                composed_from=[], skill_evolved=False, skill_version=None,
                code_executed=0, new_tasks_queued=[],
                failure_type="tool_misuse", recovery_attempted=False,
                recovery_succeeded=False,
                validation_failed=True, validation_detail=val_detail[:500],
            )
            return "validation_failed", val_detail
        else:
            print(f"  ✓ ValidationAgent passed '{name}'")
    except ImportError:
        pass  # validation_agent not available — skip

    skill = {"metadata": metadata, "body": code, "filepath": filepath}
    save_py_skill(skill)
    return "verified", skill

def llm_compile_skill(task, response_summary):
    """Ask the LLM to convert a freeform task solution into a function + test."""
    prompt = f"""Convert the following task solution into a self-contained Python module.

Task: {task}
Solution sketch: {response_summary[:1500]}

Output ONLY a Python file with:
- One top-level function with a docstring
- An `if __name__ == "__main__":` block containing assertions
- The block MUST print exactly "TEST PASSED" on success
- No external dependencies beyond the Python stdlib
- Do NOT wrap in markdown code fences

Return only the code."""
    try:
        code = _llm([{"role": "user", "content": prompt}], max_tokens=6000).strip()
        code = re.sub(r"^```\w*\s*", "", code)
        code = re.sub(r"```\s*$", "", code).strip()
        return code
    except Exception as e:
        return None

# ---------------------------------------------------------------------------
# Skill evolution (v1 -> v2)
# ---------------------------------------------------------------------------

def evolve_skill(skill, failure_trace=""):
    """Patch a failing skill via the LLM. Archive v1; persist v2 if its test passes."""
    m = skill["metadata"]
    prompt = f"""The following Python skill is failing. Diagnose and produce a fixed version.

CURRENT SKILL (v{m['version']}):
```python
{skill['body']}
```

FAILURE TRACE / CONTEXT:
{failure_trace[:1500] if failure_trace else "Skill has accumulated failures during use."}

Output ONLY the corrected Python module. It must:
- Keep the same top-level function name
- Include the same `if __name__ == "__main__":` test (or stronger)
- Print "TEST PASSED" on success
- Not be wrapped in markdown fences"""
    try:
        new_code = _llm([{"role": "user", "content": prompt}], max_tokens=6000).strip()
        new_code = re.sub(r"^```\w*\s*", "", new_code)
        new_code = re.sub(r"```\s*$", "", new_code).strip()
    except Exception as e:
        return False, f"LLM error: {e}"

    passed, output = verify_py_skill(new_code)
    if not passed:
        return False, output

    # Archive v1
    archive_path = f"{PY_SKILLS_ARCHIVE}/{m['skill']}_v{m['version']}.py"
    try:
        shutil.copy(skill["filepath"], archive_path)
    except OSError:
        pass

    new_metadata = dict(m)
    new_metadata["version"] = m["version"] + 1
    new_metadata["verified"] = True
    new_metadata["fail_count"] = 0
    new_metadata["last_used"] = _now_iso()
    new_skill = {"metadata": new_metadata, "body": new_code, "filepath": skill["filepath"]}
    save_py_skill(new_skill)
    return True, new_skill

# ---------------------------------------------------------------------------
# Skill composition
# ---------------------------------------------------------------------------

def compose_skills(task, py_skills, top_k=3):
    """Try to solve `task` by composing existing skills. Returns (composed_skill, parent_names) or (None, [])."""
    if not py_skills:
        return None, []

    # Rank by embedding similarity if possible, otherwise tag overlap
    ranked = []
    model = _get_embed_model()
    if model is not None:
        task_vec = model.encode(task).tolist()
        for s in py_skills:
            text = f"{s['metadata']['skill']} {' '.join(s['metadata'].get('tags', []))}"
            vec = model.encode(text).tolist()
            ranked.append((_cosine(task_vec, vec), s))
    else:
        task_words = set(re.findall(r"\w+", task.lower()))
        for s in py_skills:
            score = len(task_words & set(t.lower() for t in s["metadata"].get("tags", [])))
            ranked.append((score, s))
    ranked.sort(key=lambda x: x[0], reverse=True)
    k = dynamic_top_k(py_skills)
    candidates = [s for _, s in ranked[:k]]
    if not candidates:
        return None, []

    skill_blob = "\n\n".join(
        f"# {s['metadata']['skill']}\n{s['body']}" for s in candidates
    )
    prompt = f"""You are composing reusable Python skills.

TASK: {task}

EXISTING SKILLS:
{skill_blob}

Can you solve the task by COMPOSING these existing skills (importing and calling them)?
If yes, output a complete Python module that:
- Imports nothing external (inline-paste the existing functions you need)
- Defines a new top-level function that calls the others
- Has an `if __name__ == "__main__":` test that prints "TEST PASSED"

If composition is not possible, respond with exactly: NO_COMPOSITION

Do not wrap in markdown fences."""
    try:
        out = _llm([{"role": "user", "content": prompt}], max_tokens=6000).strip()
    except Exception:
        return None, []

    if "NO_COMPOSITION" in out.upper():
        return None, []
    out = re.sub(r"^```\w*\s*", "", out)
    out = re.sub(r"```\s*$", "", out).strip()
    status, result = materialize_py_skill(out, task)
    if status == "verified":
        return result, [s["metadata"]["skill"] for s in candidates]
    return None, []

# ---------------------------------------------------------------------------
# Episodic memory
# ---------------------------------------------------------------------------

_episode_cache = None

def load_episodes():
    global _episode_cache
    if _episode_cache is not None:
        return _episode_cache
    eps = []
    if os.path.exists(EPISODES_FILE):
        for line in open(EPISODES_FILE):
            line = line.strip()
            if line:
                try:
                    eps.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    _episode_cache = eps
    return eps

def save_episode(episode):
    with open(EPISODES_FILE, "a") as f:
        f.write(json.dumps(episode) + "\n")
    if _episode_cache is not None:
        _episode_cache.append(episode)

def retrieve_similar_episodes(task, k=3):
    eps = load_episodes()
    if not eps:
        return []
    model = _get_embed_model()
    if model is None:
        # Cheap fallback: substring overlap
        task_words = set(re.findall(r"\w+", task.lower()))
        scored = []
        for e in eps:
            ew = set(re.findall(r"\w+", e.get("task", "").lower()))
            overlap = len(task_words & ew)
            scored.append((overlap, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for s, e in scored[:k] if s > 0]
    task_vec = model.encode(task).tolist()
    scored = []
    for e in eps:
        ev = model.encode(e.get("task", "")).tolist()
        scored.append((_cosine(task_vec, ev), e))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for s, e in scored[:k] if s > 0.3]

# ---------------------------------------------------------------------------
# Skill decay / forgetting
# ---------------------------------------------------------------------------

def apply_decay(py_skills):
    now = datetime.now(timezone.utc)
    for s in py_skills:
        m = s["metadata"]
        try:
            last = datetime.fromisoformat(m.get("last_used", _now_iso()))
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
        except ValueError:
            last = now
        days = max(0.0, (now - last).total_seconds() / 86400.0)
        relevance = m.get("success_count", 0) / (1 + days * 0.1)
        m["decay_days"] = round(days, 2)
        m["relevance"] = round(relevance, 3)
        m["decaying"] = relevance < 0.5 and days > 7
        # Auto-archive
        if relevance < 0.1 and days > 14:
            try:
                shutil.move(s["filepath"], f"{PY_SKILLS_ARCHIVE}/{os.path.basename(s['filepath'])}")
                print(f"  [decay] Archived '{m['skill']}' (relevance={relevance:.2f})")
            except OSError:
                pass

# ---------------------------------------------------------------------------
# Target-repo context (for --target-repo experiments)
# ---------------------------------------------------------------------------

_repo_file_index_cache = {}  # repo_path -> [(path, head_text)]

def index_target_repo(repo_path, max_files=400):
    """Walk a target repo and index up to max_files Python source files with their first 10 lines."""
    if repo_path in _repo_file_index_cache:
        return _repo_file_index_cache[repo_path]
    files = []
    for root, dirs, fns in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("venv", "node_modules", "__pycache__", "tests", "docs", "site")]
        for fn in fns:
            if fn.endswith(".py"):
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, repo_path)
                try:
                    with open(full) as f:
                        head = "".join(f.readlines()[:10])
                except OSError:
                    head = ""
                files.append((rel, head))
                if len(files) >= max_files:
                    break
        if len(files) >= max_files:
            break
    _repo_file_index_cache[repo_path] = files
    return files

def top_level_tree(repo_path):
    try:
        entries = sorted(os.listdir(repo_path))
    except OSError:
        return ""
    return ", ".join(e for e in entries if not e.startswith("."))[:600]

def retrieve_relevant_files(task, repo_path, k=3):
    """Return top-k most relevant files for a task. Embedding-based, with keyword fallback."""
    files = index_target_repo(repo_path)
    if not files:
        return []
    model = _get_embed_model()
    if model is not None:
        task_vec = model.encode(task).tolist()
        scored = []
        for rel, head in files:
            text = f"{rel}\n{head[:500]}"
            vec = model.encode(text).tolist()
            scored.append((_cosine(task_vec, vec), rel, head))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(rel, head) for _, rel, head in scored[:k]]
    # Keyword fallback
    task_words = set(re.findall(r"\w+", task.lower()))
    scored = []
    for rel, head in files:
        text_words = set(re.findall(r"\w+", (rel + " " + head).lower()))
        scored.append((len(task_words & text_words), rel, head))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(rel, head) for _, rel, head in scored[:k]]

def make_repo_context(task, repo_path):
    if not repo_path or not os.path.isdir(repo_path):
        return ""
    tree = top_level_tree(repo_path)
    relevant = retrieve_relevant_files(task, repo_path, k=3)
    rel_block = "\n".join(f"  - {rel}\n    {head[:200].strip()}" for rel, head in relevant)
    return (
        f"You are working inside the repository at {repo_path}.\n"
        f"The repo top-level: {tree}\n"
        f"Relevant files for this task may include:\n{rel_block}\n\n"
    )

# ---------------------------------------------------------------------------
# Failure classification and recovery
# ---------------------------------------------------------------------------

FAILURE_TYPES = (
    "logical_inconsistency",
    "tool_misuse",
    "missing_context",
    "hallucination",
    "stylistic_misalignment",
)

RECOVERY_STRATEGIES = {
    "logical_inconsistency": "structured self-verification prompt",
    "tool_misuse": "retrieve source of misused tool and retry",
    "missing_context": "retrieve 3 more relevant files and retry",
    "hallucination": "ground output against actual source code",
    "stylistic_misalignment": "retrieve project conventions and retry",
}

def quick_self_grade(task, response):
    """Cheap 0/1/2 self-grade. Used to detect failures inline."""
    if not response or len(response.strip()) < 20:
        return 0
    prompt = f"""Score this answer 0, 1, or 2:
0 = wrong, irrelevant, or no real content
1 = partial / vague
2 = correct and specific

TASK: {task[:600]}
ANSWER: {response[:1500]}

Respond with ONLY a single digit."""
    try:
        m = re.search(r"[012]", _llm([{"role": "user", "content": prompt}], max_tokens=5))
        return int(m.group()) if m else 0
    except Exception:
        return 0

def classify_failure(task, response, signals=None):
    """Return one of FAILURE_TYPES (or None)."""
    sig_text = ""
    if signals:
        sig_text = "Signals: " + ", ".join(f"{k}={v}" for k, v in signals.items() if v)
    prompt = f"""Classify why this agent answer failed. Pick exactly one of:
- logical_inconsistency: internal contradictions, broken reasoning, or invalid logic
- tool_misuse: misused or wrongly invoked a tool/function/API
- missing_context: lacked enough source files or background to answer correctly
- hallucination: invented files, names, or APIs that don't exist in the source
- stylistic_misalignment: technically correct but doesn't match the project's conventions

TASK: {task[:600]}
ANSWER: {response[:1500]}
{sig_text}

Respond with ONLY the failure type (snake_case)."""
    try:
        raw = _llm([{"role": "user", "content": prompt}], max_tokens=20).strip().lower()
        for ft in FAILURE_TYPES:
            if ft in raw:
                return ft
    except Exception:
        pass
    return "missing_context"

def _augment_for_recovery(task, failure_type, target_repo, original_response):
    """Build an augmented prompt addendum based on the recovery strategy."""
    addendum = "\n\nRECOVERY ATTEMPT — your previous answer was judged as failing.\n"
    addendum += f"Diagnosed failure type: {failure_type}\n"
    addendum += f"Strategy: {RECOVERY_STRATEGIES[failure_type]}\n\n"

    if failure_type == "logical_inconsistency":
        addendum += (
            "Before producing a new answer, walk through these self-verification steps:\n"
            "1. State the task in your own words.\n"
            "2. List your assumptions.\n"
            "3. Check each assumption for contradictions.\n"
            "4. Then produce a corrected answer.\n"
            f"Your previous (flawed) answer was:\n{original_response[:800]}\n"
        )
    elif failure_type == "tool_misuse":
        addendum += (
            "Re-examine which function/API/tool you intended to use. State its actual signature "
            "from the source code, then retry the call correctly.\n"
            f"Previous answer:\n{original_response[:800]}\n"
        )
    elif failure_type == "missing_context":
        if target_repo:
            extra = retrieve_relevant_files(task, target_repo, k=6)[3:6]
            extra_block = "\n".join(f"  - {rel}\n    {head[:300].strip()}" for rel, head in extra)
            addendum += f"Additional relevant files from {target_repo}:\n{extra_block}\n"
        addendum += "Use these new files to ground your answer.\n"
    elif failure_type == "hallucination":
        if target_repo:
            files = repo_file_list(target_repo)[:80]
            addendum += (
                "You may have invented file paths or symbols that don't exist. "
                "Stick STRICTLY to these real files in the repo:\n"
                + "\n".join(f"  - {p}" for p in files) + "\n"
            )
    elif failure_type == "stylistic_misalignment":
        if target_repo:
            convs = sample_repo_conventions(target_repo)
            addendum += "Project conventions to match:\n" + convs + "\n"
    return addendum

_repo_filelist_cache = {}
def repo_file_list(repo_path):
    if repo_path in _repo_filelist_cache:
        return _repo_filelist_cache[repo_path]
    out = []
    for rel, _ in index_target_repo(repo_path):
        out.append(rel)
    _repo_filelist_cache[repo_path] = out
    return out

def sample_repo_conventions(repo_path, n=3):
    """Grab the head of a few real source files as convention examples."""
    files = index_target_repo(repo_path)[:n]
    return "\n".join(f"# {rel}\n{head[:500]}" for rel, head in files)

def attempt_recovery(task, original_response, failure_type, target_repo,
                     selected, md_skills, episodes):
    """Re-run the task with a recovery-augmented prompt. Return (new_response, new_exec_results)."""
    addendum = _augment_for_recovery(task, failure_type, target_repo, original_response)
    repo_ctx = make_repo_context(task, target_repo) if target_repo else ""
    full_task = (repo_ctx + task + addendum) if repo_ctx else (task + addendum)
    return run_task(full_task, selected, md_skills, episodes)


# ---------------------------------------------------------------------------
# Single-task execution (importable by experiments)
# ---------------------------------------------------------------------------

def run_single_task(task, target_repo=None, task_queue=None):
    """Execute one task through the full pipeline. Returns a result dict.
    `task_queue` (a deque) is optional; if provided, follow-up tasks get appended."""
    repo_ctx = make_repo_context(task, target_repo) if target_repo else ""
    full_task = (repo_ctx + task) if repo_ctx else task

    md_skills = load_all_skills()
    py_skills = load_py_skills()
    selected, considered = select_skills(full_task, md_skills)
    episodes = retrieve_similar_episodes(task, k=3)

    composed_skill, parents = compose_skills(task, py_skills) if py_skills else (None, [])

    response, exec_results = run_task(full_task, selected, md_skills, episodes)

    md_written = extract_and_save_skill(response)
    py_block = extract_py_skill_block(response)
    py_skill_name = None
    py_verify_failed = False
    py_status = None
    if py_block:
        py_status, result = materialize_py_skill(py_block, task)
        if py_status == "verified":
            py_skill_name = result["metadata"]["skill"]
        elif py_status == "failed":
            py_verify_failed = True
            if task_queue is not None:
                task_queue.append(f"Fix this failing skill. Error:\n{result[:500]}\n\nOriginal code:\n{py_block[:1000]}")

    new_tasks = extract_new_tasks(response)
    if task_queue is not None:
        for nt in new_tasks:
            task_queue.append(nt)

    evaluate_skill_usage(task, response, exec_results, selected)

    # ----- Failure classification + recovery -----
    failure_type = None
    recovery_attempted = False
    recovery_succeeded = False
    initial_grade = quick_self_grade(task, response)
    failed_signal = py_verify_failed or initial_grade <= 1
    if failed_signal:
        failure_type = classify_failure(task, response, signals={
            "py_verify_failed": py_verify_failed,
            "initial_grade": initial_grade,
        })
        print(f"  ⚠ failure detected → {failure_type} | strategy: {RECOVERY_STRATEGIES[failure_type]}")
        recovery_attempted = True
        try:
            new_response, new_exec = attempt_recovery(
                task, response, failure_type, target_repo,
                selected, md_skills, episodes,
            )
            new_grade = quick_self_grade(task, new_response)
            # Also try py-skill verification on the recovery output
            recovered_py = None
            new_py_block = extract_py_skill_block(new_response)
            if new_py_block:
                status, result = materialize_py_skill(new_py_block, task)
                if status == "verified":
                    recovered_py = result["metadata"]["skill"]
                    py_skill_name = recovered_py
                    py_verify_failed = False
            if new_grade > initial_grade or recovered_py:
                recovery_succeeded = True
                response = new_response
                exec_results = new_exec or exec_results
                print(f"  ✓ recovery succeeded (grade {initial_grade}→{new_grade})")
            else:
                print(f"  ✗ recovery failed (grade {initial_grade}→{new_grade})")
        except Exception as e:
            print(f"  ! recovery errored: {e}")

    outcome = "success" if (py_skill_name or composed_skill or (response and not failed_signal) or recovery_succeeded) else "fail"

    save_episode({
        "timestamp": _now_iso(),
        "task": task,
        "outcome": outcome,
        "skills_used": [s["metadata"]["name"] for s in selected],
        "py_skill_created": py_skill_name,
        "composed": bool(composed_skill),
        "evolved": False,
    })

    log_result(
        task=task, response=response, outcome=outcome,
        skills_considered=considered,
        skills_used=[s["metadata"]["name"] for s in selected],
        skill_written=md_written,
        skill_verified=py_skill_name,
        skill_verify_failed=py_verify_failed,
        skill_composed=bool(composed_skill),
        composed_from=parents,
        skill_evolved=False, skill_version=None,
        code_executed=len(exec_results) if exec_results else 0,
        new_tasks_queued=new_tasks,
        target_repo=target_repo,
        failure_type=failure_type,
        recovery_attempted=recovery_attempted,
        recovery_succeeded=recovery_succeeded,
    )

    print(f"  [BUDGET] {budget.status()} — {budget.calls_remaining()} calls remaining")
    return {
        "task": task,
        "response": response,
        "outcome": outcome,
        "skills_used": [s["metadata"]["name"] for s in selected],
        "skills_considered": considered,
        "py_skill_verified": py_skill_name,
        "py_skill_failed": py_verify_failed,
        "skill_composed": bool(composed_skill),
        "composed_from": parents,
        "code_executed": len(exec_results) if exec_results else 0,
        "exec_results": exec_results,
        "failure_type": failure_type,
        "recovery_attempted": recovery_attempted,
        "recovery_succeeded": recovery_succeeded,
    }

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def _parse_arg(flag):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None

def main():
    if "--dashboard-only" in sys.argv:
        print("Dashboard mode. Run from project root:")
        print("  python -m http.server 8080")
        print("Then open: http://localhost:8080/dashboard/")
        return

    target_repo = _parse_arg("--target-repo")
    queue_file = _parse_arg("--queue") or "tasks/task_queue.txt"

    task_queue = deque()
    for line in open(queue_file).readlines():
        line = line.strip()
        if line:
            task_queue.append(line)

    max_total_tasks = int(_parse_arg("--max-tasks") or 50)
    completed = 0

    while task_queue and completed < max_total_tasks:
        task = task_queue.popleft()
        print(f"\n{'='*60}")
        print(f"Task {completed+1}: {task}")
        print('='*60)

        # 1. Load skill libraries (markdown legacy + verified python)
        md_skills = load_all_skills()
        py_skills = load_py_skills()

        # 2. Select markdown skills (existing two-stage selection)
        selected, considered = select_skills(task, md_skills)
        print(f"  Skills considered (pre-filter): {considered}")
        if selected:
            print(f"  Skills matched (LLM ranker): {[s['metadata']['name'] for s in selected]}")

        # 3. Episodic memory retrieval
        episodes = retrieve_similar_episodes(task, k=3)
        if episodes:
            print(f"  Episodes recalled: {len(episodes)}")

        # 4. Composition check — try to solve via existing py skills first
        composed_skill, parents = compose_skills(task, py_skills) if py_skills else (None, [])
        composed_name = None
        if composed_skill:
            composed_name = composed_skill["metadata"]["skill"]
            print(f"  ✦ COMPOSED new skill '{composed_name}' from {parents}")

        # 5. Execute task (with optional target-repo context)
        repo_ctx = make_repo_context(task, target_repo) if target_repo else ""
        full_task = (repo_ctx + task) if repo_ctx else task
        response, exec_results = run_task(full_task, selected, md_skills, episodes)
        print(response[:500])

        # 6. Extract & save legacy markdown skill
        md_skill_written = extract_and_save_skill(response)
        if md_skill_written:
            print(f"  New md skill written: {md_skill_written}")

        # 7. Extract a PY SKILL block; verify; persist or queue fix
        py_skill_status = None
        py_skill_name = None
        py_verify_failed = False
        py_block = extract_py_skill_block(response)
        if not py_block and md_skill_written:
            # Fallback: compile the markdown skill into Python via the LLM
            print("  [compiling md skill to py skill via LLM...]")
            py_block = llm_compile_skill(task, response)
        if py_block:
            status, result = materialize_py_skill(py_block, task)
            py_skill_status = status
            if status == "verified":
                py_skill_name = result["metadata"]["skill"]
                print(f"  ✓ PY SKILL verified: {py_skill_name}")
            elif status == "duplicate":
                print(f"  py skill duplicate: {result}")
            else:
                py_verify_failed = True
                fix_task = f"Fix this failing skill. Error:\n{result[:500]}\n\nOriginal code:\n{py_block[:1000]}"
                task_queue.append(fix_task)
                print(f"  ✗ PY SKILL failed verification — queued fix task")

        # 8. Extract & queue any LLM-emitted follow-up tasks
        new_tasks = extract_new_tasks(response)
        for nt in new_tasks:
            print(f"  New task queued: {nt}")
            task_queue.append(nt)

        # 9. Evaluate skill usage (feedback loop on legacy md skills)
        refinement_task = evaluate_skill_usage(task, response, exec_results, selected)
        if refinement_task:
            task_queue.append(refinement_task)

        # 10. Skill evolution: any py skill with fail_count >= 2 and > success_count → evolve
        evolved_name = None
        evolved_version = None
        for s in load_py_skills():
            m = s["metadata"]
            if m.get("fail_count", 0) >= 2 and m["fail_count"] > m.get("success_count", 0):
                print(f"  ⟳ Evolving '{m['skill']}' v{m['version']}...")
                ok, result = evolve_skill(s, failure_trace=f"fail_count={m['fail_count']}")
                if ok:
                    evolved_name = result["metadata"]["skill"]
                    evolved_version = result["metadata"]["version"]
                    print(f"  ⟳ Evolved to v{evolved_version}")
                    break  # one evolution per task

        # 11. Determine outcome
        outcome = "success" if (py_skill_status == "verified" or composed_skill or exec_results or response) else "fail"
        if py_verify_failed and not (py_skill_status == "verified" or composed_skill):
            outcome = "fail"

        # 12. Save episode
        save_episode({
            "timestamp": _now_iso(),
            "task": task,
            "outcome": outcome,
            "skills_used": [s["metadata"]["name"] for s in selected],
            "py_skill_created": py_skill_name,
            "composed": bool(composed_skill),
            "evolved": bool(evolved_name),
        })

        # 13. Extended log
        log_result(
            task=task,
            response=response,
            outcome=outcome,
            skills_considered=considered,
            skills_used=[s["metadata"]["name"] for s in selected],
            skill_written=md_skill_written,
            skill_verified=py_skill_name,
            skill_verify_failed=py_verify_failed,
            skill_composed=bool(composed_skill),
            composed_from=parents,
            skill_evolved=bool(evolved_name),
            skill_version=evolved_version,
            code_executed=len(exec_results) if exec_results else 0,
            new_tasks_queued=new_tasks,
        )
        completed += 1

    print(f"\nCompleted {completed} tasks.")


if __name__ == "__main__":
    main()
