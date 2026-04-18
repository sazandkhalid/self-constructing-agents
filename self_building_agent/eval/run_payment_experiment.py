"""
Payment Rail Experiment Harness
================================
Runs the cold/warm experiment for the payment protocol domain.

Usage (from self_building_agent/ directory):
    venv/bin/python eval/run_payment_experiment.py [--max-bench N] [--max-explore N]

This script:
  1. Resets the skill library (archives existing skills_py/ contents)
  2. Runs --max-bench benchmark tasks cold (no prior skills)
  3. Resets again
  4. Runs --max-explore exploration tasks to build the skill library
  5. Runs --max-bench benchmark tasks warm (with accumulated skills)
  6. Scores both runs and writes eval/scores_payment.json

The hypothesis: warm > cold on Tier 2 and especially Tier 3 tasks.
"""

import argparse
import json
import os
import shutil
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

HERE  = Path(__file__).resolve().parent
ROOT  = HERE.parent              # self_building_agent/
sys.path.insert(0, str(ROOT))
os.chdir(str(ROOT))              # run.py expects cwd = self_building_agent/

import run as agent              # noqa: E402  (after chdir + sys.path)
import score as scorer           # noqa: E402

TARGET_REPO   = str(HERE / "target_repo" / "iso20022_synthetic")
BENCH_TASKS   = str(HERE / "payment_benchmark_tasks.txt")
EXPLORE_TASKS = str(HERE / "payment_exploration_tasks.txt")
SCORES_OUT    = str(HERE / "scores_payment.json")
LOGS_DIR      = ROOT / "logs"
SKILLS_PY     = ROOT / "skills_py"
ARCHIVE_DIR   = ROOT / "skills_py" / "archive"
BACKUP_DIR    = HERE / "backups"


def ts():
    return datetime.now(timezone.utc).strftime("%H:%M:%S")

def log(msg):
    print(f"[{ts()}] {msg}", flush=True)

def reset_state(label=""):
    """Archive current skills_py/*.py, wipe episodes, reset index.json to []."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    # Archive all current py skills
    archived = 0
    for f in SKILLS_PY.glob("*.py"):
        dst = ARCHIVE_DIR / f"{f.stem}_{stamp}.py"
        shutil.copy(f, dst)
        f.unlink()
        archived += 1

    # Reset index.json to empty list (flat list, not dict)
    idx_path = SKILLS_PY / "index.json"
    with open(idx_path, "w") as fh:
        json.dump([], fh)

    # Back up and wipe episodic memory
    episodes = ROOT / "memory" / "episodes.jsonl"
    if episodes.exists():
        shutil.copy(episodes, BACKUP_DIR / f"episodes_{stamp}.jsonl")
        episodes.unlink()
    (ROOT / "memory").mkdir(exist_ok=True)

    # Reset agent's in-memory caches
    agent._episode_cache = None
    agent._repo_file_index_cache.clear()

    log(f"State reset ({label}): archived {archived} skills, cleared episodes.")

def run_tasks(task_file, max_tasks, label, log_out):
    """Drive tasks through agent.run_single_task. Returns list of (tier, task, result)."""
    tasks = scorer.parse_task_file(task_file)[:max_tasks]
    log(f"{label}: {len(tasks)} tasks against {TARGET_REPO}")

    # Truncate the main log so log_out only captures this run's entries
    main_log = LOGS_DIR / "log.jsonl"
    LOGS_DIR.mkdir(exist_ok=True)
    main_log.write_text("")      # truncate

    results = []
    for i, (tier, task) in enumerate(tasks, 1):
        log(f"  [{i}/{len(tasks)}] ({tier}) {task[:70]}")
        t0 = time.time()
        try:
            r = agent.run_single_task(task, target_repo=TARGET_REPO)
        except Exception as e:
            log(f"    ERROR: {e}")
            r = {
                "task": task, "response": f"ERROR: {e}", "outcome": "fail",
                "skills_used": [], "skills_considered": 0,
                "py_skill_verified": None, "py_skill_failed": False,
                "skill_composed": False, "composed_from": [], "code_executed": 0,
                "exec_results": [], "failure_type": None,
                "recovery_attempted": False, "recovery_succeeded": False,
            }
        dt = time.time() - t0
        log(f"    → {r['outcome']} in {dt:.1f}s | skill={r.get('py_skill_verified')} | composed={r.get('skill_composed')}")
        results.append((tier, task, r))

    # Copy the main log to a labelled snapshot for scoring
    if main_log.exists():
        shutil.copy(main_log, log_out)
    return results

def compliance_counts_from_log(log_path):
    """Scan a log file for ComplianceShield events."""
    counts = {"pass": 0, "warn": 0, "block": 0}
    if not Path(log_path).exists():
        return counts
    for line in open(log_path):
        try:
            e = json.loads(line.strip())
        except json.JSONDecodeError:
            continue
        if e.get("compliance_block"):
            counts["block"] += 1
        elif e.get("skill_verified"):
            # Check if there's a warn flag in skills_py
            skill_name = e["skill_verified"]
            py_path = SKILLS_PY / f"{skill_name}.py"
            if py_path.exists():
                content = py_path.read_text()
                if "# compliance_warn:" in content:
                    counts["warn"] += 1
                else:
                    counts["pass"] += 1
    return counts

def main():
    parser = argparse.ArgumentParser(description="Payment Rail Cold/Warm Experiment")
    parser.add_argument("--max-bench",   type=int, default=15)
    parser.add_argument("--max-explore", type=int, default=20)
    args = parser.parse_args()

    log("=== PAYMENT RAIL EXPERIMENT START ===")
    log(f"Target repo: {TARGET_REPO}")
    log(f"Benchmark tasks: {args.max_bench} | Exploration tasks: {args.max_explore}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    cold_log  = str(HERE / f"results/cold_payment_{stamp}.jsonl")
    warm_log  = str(HERE / f"results/warm_payment_{stamp}.jsonl")
    (HERE / "results").mkdir(exist_ok=True)

    # ── COLD ────────────────────────────────────────────────────────────────
    log("--- Phase 1: COLD run ---")
    reset_state("cold")
    cold_results = run_tasks(BENCH_TASKS, args.max_bench, "COLD", cold_log)

    # ── EXPLORATION ─────────────────────────────────────────────────────────
    log("--- Phase 2: Exploration (building skill library) ---")
    reset_state("explore")
    skills_before = set(SKILLS_PY.glob("*.py"))
    run_tasks(EXPLORE_TASKS, args.max_explore, "EXPLORE", str(HERE / f"results/explore_{stamp}.jsonl"))
    skills_after  = set(SKILLS_PY.glob("*.py"))
    new_skills    = [p.name for p in skills_after - skills_before]
    log(f"Exploration produced {len(new_skills)} new verified skills: {new_skills}")

    # ── WARM ────────────────────────────────────────────────────────────────
    log("--- Phase 3: WARM run ---")
    warm_results = run_tasks(BENCH_TASKS, args.max_bench, "WARM", warm_log)

    # ── SCORE ────────────────────────────────────────────────────────────────
    log("--- Scoring ---")
    cold_scored = [scorer.score_one(t, q, r, TARGET_REPO, payment_domain=True)
                   for t, q, r in cold_results]
    warm_scored = [scorer.score_one(t, q, r, TARGET_REPO, payment_domain=True)
                   for t, q, r in warm_results]
    cold_agg    = scorer.aggregate(cold_scored)
    warm_agg    = scorer.aggregate(warm_scored)

    def delta(tier):
        return warm_agg["by_tier"].get(tier, 0.0) - cold_agg["by_tier"].get(tier, 0.0)

    improvement_pct = 0.0
    if cold_agg["avg"] > 0:
        improvement_pct = (warm_agg["avg"] - cold_agg["avg"]) / cold_agg["avg"] * 100.0

    compliance = compliance_counts_from_log(warm_log)

    summary = {
        "cold_avg":  round(cold_agg["avg"], 3),
        "warm_avg":  round(warm_agg["avg"], 3),
        "improvement_pct": round(improvement_pct, 1),
        "tier1_delta": round(delta("TIER1"), 3),
        "tier2_delta": round(delta("TIER2"), 3),
        "tier3_delta": round(delta("TIER3"), 3),
        "cold_by_tier": {k: round(v, 3) for k, v in cold_agg["by_tier"].items()},
        "warm_by_tier": {k: round(v, 3) for k, v in warm_agg["by_tier"].items()},
        "skills_built_during_exploration": len(new_skills),
        "skills_used_in_warm": sum(1 for s in warm_scored if s["used_verified_skill"]),
        "compositions": sum(1 for s in warm_scored if s["skill_composed"]),
        "compliance_pass":  compliance["pass"],
        "compliance_warn":  compliance["warn"],
        "compliance_block": compliance["block"],
    }

    out = {
        "experiment": "payment_rail",
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "config":     {"max_bench": args.max_bench, "max_explore": args.max_explore},
        "cold":  cold_scored,
        "warm":  warm_scored,
        "summary": summary,
    }
    with open(SCORES_OUT, "w") as fh:
        json.dump(out, fh, indent=2)
    log(f"Results → {SCORES_OUT}")

    # ── QUICK SUMMARY ────────────────────────────────────────────────────────
    log("=== QUICK RESULTS ===")
    log(f"COLD avg: {summary['cold_avg']:.2f}/3.0")
    log(f"WARM avg: {summary['warm_avg']:.2f}/3.0  ({improvement_pct:+.1f}%)")
    log(f"Tier 1 Δ: {summary['tier1_delta']:+.2f}  Tier 2 Δ: {summary['tier2_delta']:+.2f}  Tier 3 Δ: {summary['tier3_delta']:+.2f}")
    log(f"Skills built: {summary['skills_built_during_exploration']}  Used in warm: {summary['skills_used_in_warm']}")
    log(f"ComplianceShield — PASS: {compliance['pass']}  WARN: {compliance['warn']}  BLOCK: {compliance['block']}")
    if summary["warm_avg"] > summary["cold_avg"]:
        log("HYPOTHESIS SUPPORTED: warm > cold")
    elif summary["warm_avg"] == summary["cold_avg"]:
        log("HYPOTHESIS INCONCLUSIVE: warm == cold")
    else:
        log("HYPOTHESIS NOT SUPPORTED: warm < cold")
    log("Run: venv/bin/python eval/report.py --payment")
    log("=== EXPERIMENT COMPLETE ===")


if __name__ == "__main__":
    main()
