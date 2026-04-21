# self-constructing-agents

A research system testing the hypothesis: **an LLM agent that accumulates a repo-specific skill library performs measurably better on coding tasks than one starting cold.**

---

## Setup (fresh clone)

```bash
git clone https://github.com/sazandkhalid/self-constructing-agents.git
cd self-constructing-agents/self_building_agent

# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Get a free Groq API key at https://console.groq.com
#    then set it (or add it to .env):
export GROQ_API_KEY=your_key_here
```

---

## FastAPI Experiment

Tests the core hypothesis against [FastAPI](https://github.com/tiangolo/fastapi) source code tasks.

### One-time: clone the target repo

```bash
# from inside self_building_agent/
git clone --depth=1 https://github.com/tiangolo/fastapi.git eval/target_repo/fastapi
```

### Quick smoke test (3 tasks each, ~5 minutes)

```bash
venv/bin/python eval/run_experiment.py --max-bench 3 --max-explore 3
venv/bin/python eval/report.py
```

### Full experiment (15 benchmark + 20 exploration, ~45 minutes)

```bash
venv/bin/python eval/run_experiment.py
venv/bin/python eval/report.py
```

### What it tests

Three task tiers against the FastAPI codebase:

- **Tier 1 — Structural**: read and describe real functions, signatures, and patterns
- **Tier 2 — Pattern**: apply FastAPI patterns to write new code
- **Tier 3 — Novel**: synthesise cross-cutting knowledge from accumulated skills

---

## Payment Rail Experiment

Tests the core hypothesis against financial protocol integration tasks using a synthetic ISO 20022 / ACH codebase (no external clone needed — the target repo is included at `eval/target_repo/iso20022_synthetic/`).

### Quick smoke test (3 tasks each)

```bash
venv/bin/python eval/run_payment_experiment.py --max-bench 3 --max-explore 3
venv/bin/python eval/report.py --payment
```

### Full experiment (15 benchmark + 20 exploration)

```bash
venv/bin/python eval/run_payment_experiment.py
venv/bin/python eval/report.py --payment
```

### What it tests

Three task tiers against the synthetic ISO 20022 / ACH codebase:

- **Tier 1 — Structural**: read the target repo, extract correct information about functions, signatures, and constants
- **Tier 2 — Translation**: write code that bridges between payment formats (ISO 20022 XML → LedgerEntry, ACHEntry → LedgerEntry, address normalisation, cross-rail reconciliation)
- **Tier 3 — Synthesis**: abstract reusable patterns from accumulated knowledge (generic validators, dispatcher functions, builder classes, safe-parse utilities)

The hypothesis is that a warm agent (one that has built a skill library during the exploration phase) will score measurably higher on Tier 2 and Tier 3 tasks than a cold agent starting from zero. The Tier 3 delta is the headline signal.

### New skill metadata fields

Payment-domain skills carry additional header fields:

```
# protocol: iso20022|ach|fedwire|sepa|internal|general
# rail: swift_mx|fednow|rtp|nacha|sepa_ct|on_chain|general
# audit_required: true|false
```

### ComplianceShield

Every payment skill passes through a static analysis check (`compliance.py`) before persisting:

- **BLOCK**: hardcoded routing numbers, IBANs, passwords, SSN patterns, or API keys → skill is rejected and not written to disk
- **WARN**: skill accesses financial/PII data (`account_number`, `iban`, `debtor`, etc.) without a logging hook → persisted with a `compliance_warn` metadata flag
- **PASS**: no issues detected → persisted normally

The shield is static analysis only — no LLM calls, no execution.

---

## Architecture

The agent loop (`run.py`, ~1500 lines) layers the following systems:

| Layer | File | Purpose |
|---|---|---|
| Core loop | `run.py` | Task queue → LLM → skill extraction → verify → persist |
| Verified skills | `skills_py/` | Executable Python functions with `TEST PASSED` gate |
| Markdown skills | `skills/` | Conceptual patterns (legacy) |
| ComplianceShield | `compliance.py` | Static PII/credential check before persist |
| ValidationAgent | `validation_agent.py` | Adversarial LLM edge-case tests before persist |
| MCP tools | `mcp_client.py` | 4 builtin tools + agent-built tool registration |
| RAG | `rag.py` | Financial spec document retrieval injected into prompts |
| Entity memory | `entity_memory.py` | Per-institution quirks and failure patterns |
| Episodic memory | `memory/episodes.jsonl` | Semantic retrieval of past task outcomes |
| Skill evolution | `run.py:evolve_skill` | LLM-patches failing skills (v1 → v2) |
| Skill decay | `run.py:apply_decay` | Auto-archives stale low-success skills |
| Dashboard | `dashboard/index.html` | Canvas terrain map of the skill library |

### Dashboard

```bash
# from self_building_agent/
python -m http.server 8080
# open http://localhost:8080/dashboard/
```

Dark sci-fi terrain map showing skill nodes, evolution timeline, activity feed, and skill registry. Reads from `logs/log.jsonl` and `skills_py/`.

---

## API key

Both experiments call the [Groq API](https://console.groq.com) using `llama-3.3-70b-versatile`. A free tier account gives 100K tokens/day — enough for the smoke test. The full experiment (~35 tasks) may require waiting for the daily limit to reset or upgrading to a paid plan.
