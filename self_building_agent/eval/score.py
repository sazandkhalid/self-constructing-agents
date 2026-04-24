"""Score cold vs warm results for the experiment.

Can be used as a module (imported by run_experiment.py) or as a CLI:
    python eval/score.py --log logs/run_cold.jsonl --tasks eval/payment_benchmark_tasks.txt \
        --out eval/scores_cold.json --target-repo eval/target_repo/iso20022_synthetic \
        --payment-domain
"""
import os, sys, json, re, ast, subprocess, tempfile, argparse, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from google import genai
from google.genai import types as genai_types
_gemini = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
_MODEL  = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

LOG_FILE = os.path.join("logs", "log.jsonl")
SKILLS_PY_DIR = "skills_py"

# Payment-domain symbols that confirm the agent read the target repo
PAYMENT_SYMBOLS = [
    "PACS_008", "PACS_009", "PACS_002", "CAMT_053", "CAMT_054", "PAIN_001", "PAIN_002",
    "parse_pacs008", "extract_statement_entries", "validate_routing_number",
    "match_by_reference", "surface_exceptions", "validate_hybrid_address",
    "parse_unstructured_address", "build_ach_file", "format_ach_amount",
    "LedgerEntry", "MatchResult", "CreditTransfer", "HybridAddress", "ACHEntry", "ACHBatch",
]

_repo_files_cache = {}

def repo_files(target_repo=None):
    key = target_repo or "__default__"
    if key in _repo_files_cache:
        return _repo_files_cache[key]
    search_root = target_repo or os.path.join("eval", "target_repo", "fastapi")
    files = set()
    for root, dirs, fns in os.walk(search_root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in fns:
            if fn.endswith(".py"):
                rel = os.path.relpath(os.path.join(root, fn), search_root)
                files.add(rel)
                files.add(os.path.basename(rel))
    _repo_files_cache[key] = files
    return files

def parse_task_file(path):
    """Parse a task file into list of (tier, task_text).
    Supports both TIER1::task and # TIER N: comment-header formats.
    """
    tasks = []
    current_tier = "UNTIERED"
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("##"):
            continue
        # Comment-style tier header: # TIER 1: ...
        m = re.match(r"#\s*TIER\s*(\d+)", line, re.I)
        if m:
            current_tier = f"TIER{m.group(1)}"
            continue
        if line.startswith("#"):
            continue
        # Inline prefix format: TIER1::task or EXPLORE::task
        if "::" in line:
            prefix, body = line.split("::", 1)
            prefix = prefix.strip().upper()
            if prefix.startswith("TIER"):
                current_tier = prefix
            tasks.append((current_tier, body.strip()))
        else:
            tasks.append((current_tier, line))
    return tasks

def llm_judge(task, response, domain="fastapi"):
    """Return (0|1|2, reasoning). domain affects the rubric framing."""
    domain_hint = "FastAPI repository" if domain == "fastapi" else "ISO 20022/ACH payment codebase"
    prompt = f"""You are scoring an agent's answer to a coding task about the {domain_hint}.

TASK: {task}

AGENT ANSWER:
{response[:3000]}

Score 0, 1, or 2:
- 0: wrong, irrelevant, hallucinated, or no concrete content
- 1: partially correct — vague, missing detail, or only partially answers
- 2: correct, specific, and grounded in real code from the target codebase

Respond with ONLY a JSON object: {{"score": 0|1|2, "reasoning": "one sentence"}}"""
    for attempt in range(4):
        try:
            r = _gemini.models.generate_content(
                model=_MODEL, contents=prompt,
                config=genai_types.GenerateContentConfig(max_output_tokens=200),
            )
            raw = r.text.strip()
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                obj = json.loads(m.group())
                return int(obj.get("score", 0)), obj.get("reasoning", "")
            return 0, "no parse"
        except Exception as e:
            msg = str(e)
            if "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
                wait = 15 * (2 ** attempt)
                time.sleep(wait)
            else:
                return 0, f"judge error: {e}"
    return 0, "judge error: max retries exceeded"

def code_executes(response):
    """Try to extract any python code block and run it. Returns True iff exit 0."""
    blocks = re.findall(r"```python\n(.*?)```", response, re.DOTALL)
    if not blocks:
        blocks = re.findall(r"---EXECUTE---\s*```python\n(.*?)```\s*---END EXECUTE---", response, re.DOTALL)
    if not blocks:
        return False
    code = blocks[0]
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        r = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=15)
        return r.returncode == 0
    except Exception:
        return False
    finally:
        try: os.unlink(path)
        except OSError: pass

def references_real_files(response, target_repo=None):
    files = repo_files(target_repo)
    text = response or ""
    for f in files:
        if f and f in text:
            return True
    return bool(re.search(r"[\w/]+\.py", text) and any(f.split("/")[-1] in text for f in files))

def references_payment_symbols(response):
    """Return True if response mentions any known payment-domain symbol."""
    text = response or ""
    return any(sym in text for sym in PAYMENT_SYMBOLS)

def used_verified_skill(result):
    return bool(result.get("py_skill_verified")) or bool(result.get("skill_composed"))

def score_one(tier, task, result, target_repo=None, payment_domain=False):
    response = result.get("response", "") or ""
    domain = "payment" if payment_domain else "fastapi"
    judge_score, reasoning = llm_judge(task, response, domain=domain)
    bonus_exec  = 1 if code_executes(response) else 0
    bonus_files = 1 if references_real_files(response, target_repo) else 0
    bonus_skill = 1 if used_verified_skill(result) else 0
    bonus_payment = 0
    if payment_domain:
        bonus_payment = 1 if references_payment_symbols(response) else 0

    raw = judge_score + bonus_exec + bonus_files + bonus_skill + bonus_payment
    final = min(3, raw)
    return {
        "tier": tier,
        "task": task,
        "score": final,
        "judge_score": judge_score,
        "exec_ok": bool(bonus_exec),
        "refs_real_files": bool(bonus_files),
        "used_verified_skill": bool(bonus_skill),
        "refs_payment_symbols": bool(bonus_payment),
        "reasoning": reasoning,
        "py_skill_verified": result.get("py_skill_verified"),
        "skill_composed": result.get("skill_composed"),
        "failure_type": result.get("failure_type"),
        "recovery_attempted": bool(result.get("recovery_attempted")),
        "recovery_succeeded": bool(result.get("recovery_succeeded")),
    }

def aggregate(scored):
    if not scored:
        return {"avg": 0.0, "by_tier": {}}
    by_tier = {}
    for s in scored:
        by_tier.setdefault(s["tier"], []).append(s["score"])
    return {
        "avg": sum(s["score"] for s in scored) / len(scored),
        "by_tier": {t: sum(v)/len(v) for t, v in by_tier.items()},
    }

def score_all(cold_results, warm_results, summary_extra=None,
              out_path="eval/results/scores.json",
              target_repo=None, payment_domain=False):
    cold_scored = [score_one(t, q, r, target_repo, payment_domain) for (t, q, r) in cold_results]
    warm_scored = [score_one(t, q, r, target_repo, payment_domain) for (t, q, r) in warm_results]
    cold_agg = aggregate(cold_scored)
    warm_agg = aggregate(warm_scored)

    skills_used_in_warm = sum(1 for s in warm_scored if s["used_verified_skill"])
    compositions = sum(1 for s in warm_scored if s["skill_composed"])

    improvement_pct = 0.0
    if cold_agg["avg"] > 0:
        improvement_pct = ((warm_agg["avg"] - cold_agg["avg"]) / cold_agg["avg"]) * 100.0

    def delta(t):
        return warm_agg["by_tier"].get(t, 0.0) - cold_agg["by_tier"].get(t, 0.0)

    summary = {
        "cold_avg": round(cold_agg["avg"], 3),
        "warm_avg": round(warm_agg["avg"], 3),
        "improvement_pct": round(improvement_pct, 1),
        "tier1_delta": round(delta("TIER1"), 3),
        "tier2_delta": round(delta("TIER2"), 3),
        "tier3_delta": round(delta("TIER3"), 3),
        "cold_by_tier": {k: round(v, 3) for k, v in cold_agg["by_tier"].items()},
        "warm_by_tier": {k: round(v, 3) for k, v in warm_agg["by_tier"].items()},
        "skills_used_in_warm": skills_used_in_warm,
        "compositions": compositions,
    }
    if summary_extra:
        summary.update(summary_extra)
    out = {"cold": cold_scored, "warm": warm_scored, "summary": summary}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    return out

def load_log_results(log_path, task_list):
    """Load run results from a jsonl log file, aligned to a task list.
    Returns list of (tier, task, result_dict).
    """
    entries = []
    if os.path.exists(log_path):
        for line in open(log_path):
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # Align log entries to task list by task text match
    results = []
    used_indices = set()
    for tier, task in task_list:
        matched = None
        for i, e in enumerate(entries):
            if i not in used_indices and task.lower()[:80] in (e.get("task") or "").lower()[:120]:
                matched = e
                used_indices.add(i)
                break
        if matched is None:
            matched = {"task": task, "response": "", "outcome": "no_log"}
        results.append((tier, task, matched))
    return results

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Score a cold or warm agent run")
    parser.add_argument("--log",          required=True,  help="Path to run log (jsonl)")
    parser.add_argument("--tasks",        required=True,  help="Path to task file")
    parser.add_argument("--out",          required=True,  help="Output scores JSON path")
    parser.add_argument("--target-repo",  default=None,   help="Path to target repo for file-reference check")
    parser.add_argument("--payment-domain", action="store_true", help="Enable payment-domain scoring bonus")
    parser.add_argument("--label",        default="run",  help="Label for this run (cold/warm/explore)")
    args = parser.parse_args()

    os.chdir(ROOT)  # score.py always runs relative to project root

    task_list = parse_task_file(args.tasks)
    results   = load_log_results(args.log, task_list)
    scored    = [score_one(t, q, r, args.target_repo, args.payment_domain)
                 for (t, q, r) in results]
    agg       = aggregate(scored)

    out = {
        "label": args.label,
        "scores": scored,
        "summary": {
            "avg": round(agg["avg"], 3),
            "by_tier": {k: round(v, 3) for k, v in agg["by_tier"].items()},
            "tasks_scored": len(scored),
        },
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Scored {len(scored)} tasks → avg {agg['avg']:.2f}. Written to {args.out}")

if __name__ == "__main__":
    main()
