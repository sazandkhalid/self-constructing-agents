# Self-Constructing Agents

An AI agent that builds, verifies, and accumulates a permanent library of executable Python skills as a by-product of normal task execution — and reuses them through composition, evolution, and decay.

**Ihsan Alaeddin · Sazan Khalid · Georgetown University · DSAN 6725 · 2026**

---

## What it does

Every time the agent solves a task it tries to extract a reusable Python function from its response, run it through a five-gate verification pipeline, and persist it to a growing skill library. On subsequent tasks it selects relevant skills from the library and injects them as context, making it progressively better at the problems it has already seen.

Key behaviours:

- **Skill creation** — agent emits `---PY SKILL---` blocks; functions are AST-parsed, executed, compliance-checked, and adversarially tested before saving
- **Skill reuse** — two-stage selector (keyword filter → embedding cosine rank → LLM ranker) surfaces relevant skills for each new task
- **Skill evolution** — skills that accumulate failures are automatically patched by the LLM and re-verified
- **Skill decay** — skills unused for 14+ days with low relevance scores are archived, keeping the library lean
- **Tool authoring** — when a capability is missing the agent authors a new MCP tool, runs it through the same four gates, registers it, and calls it in the same turn
- **RAG** — seven seeded financial-spec documents (ISO 20022, NACHA ACH, SWIFT MX, PCI/GDPR) are retrieved at query time and injected into context

---

## Results

Cold/warm experiment on the FastAPI codebase (6 benchmark tasks across three tiers):

| Condition | Avg score / 3.0 |
|-----------|----------------|
| Cold (empty library) | 2.00 |
| Warm (6 skills built) | 2.67 |
| **Improvement** | **+33.3%** |

Tier 1 (structural) showed the strongest gain: cold 1.50 → warm 2.50 (+1.00).

---

## Repository layout

```
self-constructing-agents/
├── run.py                      # Agent core — LLM loop, skill lifecycle, failure recovery
├── ask.py                      # Interactive single-task entry point (demo)
├── compliance.py               # ComplianceShield — static safety gate before skill persist
├── validation_agent.py         # ValidationAgent — adversarial LLM edge-case testing
├── mcp_client.py               # MCP tool layer — built-in tools + agent-built tool registry
├── rag.py                      # RAG layer — financial spec document retrieval
├── entity_memory.py            # Entity memory — institution-specific facts
├── payment_trace.py            # Payment simulation trace writer
│
├── eval/
│   ├── run_experiment.py       # Cold/warm experiment harness
│   ├── score.py                # LLM-as-judge scorer
│   ├── report.py               # Human-readable report printer
│   ├── benchmark_tasks.txt     # FastAPI benchmark (15 tasks, 3 tiers)
│   ├── payment_benchmark_tasks.txt
│   ├── exploration_tasks.txt
│   ├── payment_exploration_tasks.txt
│   └── target_repo/            # Cloned repos used as benchmark context
│
├── skills_py/                  # Verified Python skills (auto-managed)
│   ├── index.json
│   └── archive/
│
├── skills/                     # Markdown skills (legacy)
├── tools/                      # Agent-built MCP tool registry
│   └── registry.json
│
├── prompts/
│   └── interactive_task_addendum.txt   # Capability-discovery protocol for ask.py
│
├── rag/
│   └── documents.json          # Seeded financial spec documents
│
├── logs/
│   └── log.jsonl               # Structured run log
│
├── memory/
│   └── episodes.jsonl          # Episodic memory
│
├── dashboard/                  # Live payment simulation visualisation
├── slides/                     # 14-slide presentation deck
├── poster/                     # Conference poster
└── .env                        # API keys (not committed)
```

---

## Setup

**Requirements:** Python 3.11+

```bash
# Clone
git clone https://github.com/sazankhalid/self-constructing-agents
cd self-constructing-agents

# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install google-genai yfinance
```

**Configure `.env`:**

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_BUDGET_USD=5.00
HF_TOKEN=your_hf_token_here        # optional — removes HuggingFace rate limits
```

Get a free Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

---

## Try it

### Single-task interactive mode

```bash
source venv/bin/activate

# Fetches live stock price — agent authors a fetch_stock_price tool on first run
python ask.py "fetch the current price of AAPL and compute its 5-day moving average"

# Uses free open-meteo API — agent authors a fetch_weather tool
python ask.py "fetch the current temperature in San Francisco"

# Reuses the validate_iban skill if it exists, or authors a new tool
python ask.py "validate this IBAN: GB82WEST12345698765432"
```

The agent will:
1. Check whether an existing skill or tool can solve the task
2. If not, author a new MCP tool, run it through the four-gate pipeline, and call it
3. Print gate-by-gate verification output and the final answer

### Cold/warm experiment (FastAPI benchmark)

```bash
source venv/bin/activate

EXPLORE_TASKS_FILE=eval/exploration_tasks.txt \
  python eval/run_experiment.py --max-bench 6 --max-explore 20

python eval/report.py
```

### Payment simulation (ISO 20022 — no API required)

```bash
python3 -m http.server 8080 --directory .
open http://localhost:8080/dashboard/payment_simulation.html
```

---

## The five-gate verification pipeline

Every skill and agent-built tool passes all five gates or is rejected:

| Gate | Check |
|------|-------|
| 1. AST validity | Code parses without `SyntaxError` |
| 2. Subprocess test | Code executes and prints `TEST PASSED` |
| 3. Schema validation | Tools: `input_schema` and `output_schema` present with descriptions |
| 4. ComplianceShield | No hardcoded credentials, routing numbers, IBANs, or SSNs |
| 5. ValidationAgent | LLM generates 6 adversarial edge-case tests; all must pass |

Skills and tools that fail any gate are not persisted. Tools that fail gates 1–4 are retried up to three times — the failure gate and error message are fed back to the model so it can correct its implementation.

---

## Architecture

```
Task
 │
 ├─ RAG retrieval (7 financial spec docs)
 ├─ Skill selection (keyword → embedding → LLM ranker)
 ├─ Episodic memory retrieval
 │
 └─ LLM response loop (max 3 iterations)
      │
      ├─ Tool authoring?  → register_agent_tools() → 4-gate verify → registry.json
      ├─ Tool call?       → dispatch_agent_tool()  → run function with real args
      ├─ EXECUTE block?   → subprocess execution   → result fed back
      │
      └─ Final response
           │
           ├─ PY SKILL block → materialize_py_skill() → 5-gate verify → skills_py/
           ├─ Failure detected? → classify → recovery attempt
           └─ log_result() → logs/log.jsonl
```

---

## MCP tool authoring format

When the agent needs a capability that does not exist, it emits:

```
---MCP TOOL---
name: fetch_stock_price
description: Fetch the current price and recent history for a stock ticker
input_schema:
  ticker:
    type: string
    description: Stock ticker symbol e.g. AAPL
output_schema:
  current:
    type: number
    description: Current price in USD
code: |
  import yfinance as yf

  def fetch_stock_price(ticker: str) -> dict:
      stock = yf.Ticker(ticker)
      hist = stock.history(period="1d")
      return {"current": float(hist["Close"].iloc[-1])}

  if __name__ == "__main__":
      r = fetch_stock_price("AAPL")
      assert isinstance(r["current"], float) and r["current"] > 0
      print("TEST PASSED")
---END MCP TOOL---
```

Then calls it:

```
---TOOL CALL---
{"tool": "fetch_stock_price", "args": {"ticker": "AAPL"}}
---END TOOL CALL---
```

Registered tools persist to `tools/registry.json` and are available on all subsequent runs.

---

## Presentation and poster

```bash
# Start the file server (if not already running)
python3 -m http.server 8080 --directory .

# 14-slide deck (arrow keys / scroll to navigate)
open http://localhost:8080/slides/index.html

# Conference poster
open http://localhost:8080/poster/index.html

# Live payment simulation dashboard
open http://localhost:8080/dashboard/payment_simulation.html
```
