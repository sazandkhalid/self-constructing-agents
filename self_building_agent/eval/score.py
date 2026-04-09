"""Score cold vs warm results for the experiment."""
import os, sys, json, re, ast, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from groq import Groq
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

TARGET_REPO = os.path.join("eval", "target_repo", "fastapi")
LOG_FILE = os.path.join("logs", "log.jsonl")
SKILLS_PY_DIR = "skills_py"

_repo_files_cache = None

def repo_files():
    global _repo_files_cache
    if _repo_files_cache is not None:
        return _repo_files_cache
    files = set()
    for root, dirs, fns in os.walk(TARGET_REPO):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in fns:
            if fn.endswith(".py"):
                rel = os.path.relpath(os.path.join(root, fn), TARGET_REPO)
                files.add(rel)
                files.add(os.path.basename(rel))
    _repo_files_cache = files
    return files

def llm_judge(task, response):
    """Return (0|1|2, reasoning)."""
    prompt = f"""You are scoring an agent's answer to a task about the FastAPI repository.

TASK: {task}

AGENT ANSWER:
{response[:3000]}

Score 0, 1, or 2:
- 0: wrong, irrelevant, hallucinated, or no concrete content
- 1: partially correct — vague, missing detail, or only partially answers
- 2: correct, specific, and grounded in real fastapi structure

Respond with ONLY a JSON object: {{"score": 0|1|2, "reasoning": "one sentence"}}"""
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = r.choices[0].message.content.strip()
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            obj = json.loads(m.group())
            return int(obj.get("score", 0)), obj.get("reasoning", "")
    except Exception as e:
        return 0, f"judge error: {e}"
    return 0, "no parse"

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
        r = subprocess.run(["python3", path], capture_output=True, text=True, timeout=15)
        return r.returncode == 0
    except Exception:
        return False
    finally:
        try: os.unlink(path)
        except OSError: pass

def references_real_files(response):
    files = repo_files()
    text = response or ""
    for f in files:
        if f and f in text:
            return True
    # Also accept fastapi/<file>.py mentions
    return bool(re.search(r"fastapi/[\w/]+\.py", text))

def used_verified_skill(result):
    return bool(result.get("py_skill_verified")) or bool(result.get("skill_composed"))

def score_one(tier, task, result):
    response = result.get("response", "") or ""
    judge_score, reasoning = llm_judge(task, response)        # 0..2
    bonus_exec = 1 if code_executes(response) else 0          # +1
    bonus_files = 1 if references_real_files(response) else 0  # +1 (we'll cap)
    bonus_skill = 1 if used_verified_skill(result) else 0     # +1
    # Cap at 3 as the spec asks for 0-3 range; we squash bonuses
    raw = judge_score + bonus_exec + bonus_files + bonus_skill
    final = min(3, raw)
    return {
        "tier": tier,
        "task": task,
        "score": final,
        "judge_score": judge_score,
        "exec_ok": bool(bonus_exec),
        "refs_real_files": bool(bonus_files),
        "used_verified_skill": bool(bonus_skill),
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

def count_skill_usage_in_log():
    if not os.path.exists(LOG_FILE):
        return 0, 0
    used = 0
    composed = 0
    for line in open(LOG_FILE):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("skill_verified"):
            used += 1
        if e.get("skill_composed"):
            composed += 1
    return used, composed

def score_all(cold_results, warm_results, summary_extra=None, out_path="eval/results/scores.json"):
    cold_scored = [score_one(t, q, r) for (t, q, r) in cold_results]
    warm_scored = [score_one(t, q, r) for (t, q, r) in warm_results]
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

if __name__ == "__main__":
    print("score.py is invoked from run_experiment.py — nothing to do standalone.")
