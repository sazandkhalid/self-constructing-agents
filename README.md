# self-constructing-agents

A research system testing the hypothesis: **an LLM agent that accumulates a repo-specific skill library performs measurably better on coding tasks than one starting cold.**

## Quick start

```bash
cd self_building_agent
export GROQ_API_KEY=...
venv/bin/python eval/run_experiment.py --max-bench 3 --max-explore 3
venv/bin/python eval/report.py
```

## FastAPI experiment

Tests the core hypothesis against FastAPI source code tasks.

### Full experiment (15 benchmark + 20 exploration)

```bash
venv/bin/python eval/run_experiment.py
venv/bin/python eval/report.py
```

---

## Payment Rail Experiment

Tests the core hypothesis against financial protocol integration tasks using an ISO 20022 / ACH synthetic codebase.

### Setup

```bash
pip install schwifty faker
```

(`python-iso20022` is not available on PyPI; the experiment uses a synthetic target repo under `eval/target_repo/iso20022_synthetic/`.)

### Quick smoke test (3 tasks each)

```bash
set -a && . ./.env && set +a
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

### Dashboard

```bash
python -m http.server 8080
# open http://localhost:8080/dashboard/
```

Dark sci-fi terrain map showing skill nodes, evolution timeline, activity feed, and skill registry. Reads from `logs/log.jsonl` and `skills_py/`.
