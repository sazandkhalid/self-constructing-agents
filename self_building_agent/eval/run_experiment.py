"""Cold vs Warm experiment for the self-constructing agent.

Run from the self_building_agent/ directory:
    venv/bin/python eval/run_experiment.py [--max-explore N] [--max-bench N]
    venv/bin/python eval/run_experiment.py --resume-warm
    venv/bin/python eval/run_experiment.py --resume-cold

Override exploration tasks:
    EXPLORE_TASKS_FILE=eval/exploration_tasks_simple.txt venv/bin/python eval/run_experiment.py ...

Override model:
    ANTHROPIC_MODEL=claude-haiku-4-5-20251001 venv/bin/python eval/run_experiment.py ...
"""
import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import run as agent  # noqa

TARGET_REPO  = ROOT / "eval" / "target_repo" / "fastapi"
BENCH_FILE   = ROOT / "eval" / "benchmark_tasks.txt"
_default_explore = os.environ.get("EXPLORE_TASKS_FILE", str(ROOT / "eval" / "exploration_tasks.txt"))
EXPLORE_FILE = Path(_default_explore)
RESULTS_DIR  = ROOT / "eval" / "results"
COLD_DIR     = RESULTS_DIR / "cold"
WARM_DIR     = RESULTS_DIR / "warm"
BACKUP_DIR   = ROOT / "eval" / "backups"
SKILLS_PY    = ROOT / "skills_py"


def load_tasks(path):
    tasks = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "::" in line:
            tier, body = line.split("::", 1)
            tasks.append((tier.strip(), body.strip()))
        else:
            tasks.append(("UNTIERED", line))
    return tasks


def count_skills() -> int:
    idx = SKILLS_PY / "index.json"
    if not idx.exists():
        return 0
    data = json.loads(idx.read_text())
    return len(data) if isinstance(data, list) else len(data.get("skills", []))


def reset_state():
    """Wipe skills_py/ and memory/episodes.jsonl, backing up any existing state."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    if SKILLS_PY.is_dir() and any(SKILLS_PY.iterdir()):
        dst = BACKUP_DIR / f"skills_py_{stamp}"
        shutil.copytree(SKILLS_PY, dst)
    shutil.rmtree(SKILLS_PY, ignore_errors=True)
    (SKILLS_PY / "archive").mkdir(parents=True, exist_ok=True)

    episodes = ROOT / "memory" / "episodes.jsonl"
    if episodes.exists():
        shutil.copy(episodes, BACKUP_DIR / f"episodes_{stamp}.jsonl")
        episodes.unlink()
    (ROOT / "memory").mkdir(parents=True, exist_ok=True)

    agent._episode_cache = None
    agent._repo_file_index_cache.clear()


def save_result(out_dir, idx, tier, task, result):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    payload = {
        "index": idx,
        "tier": tier,
        "task": task,
        **{k: v for k, v in result.items() if k != "exec_results"},
        "exec_results_count": len(result.get("exec_results") or []),
    }
    with open(Path(out_dir) / f"task_{idx:02d}.json", "w") as f:
        json.dump(payload, f, indent=2, default=str)


def run_condition(label, tasks, out_dir, target_repo):
    print(f"\n{'#'*70}\n# {label}: {len(tasks)} benchmark tasks\n{'#'*70}")
    results = []
    for i, (tier, task) in enumerate(tasks, 1):
        print(f"\n[{label}] {i}/{len(tasks)} ({tier}) {task[:80]}")
        t0 = time.time()
        try:
            r = agent.run_single_task(task, target_repo=str(target_repo))
        except Exception as e:
            print(f"  ! task errored: {e}")
            r = {"task": task, "response": f"ERROR: {e}", "outcome": "fail",
                 "skills_used": [], "skills_considered": 0,
                 "py_skill_verified": None, "py_skill_failed": False,
                 "skill_composed": False, "composed_from": [], "code_executed": 0,
                 "exec_results": []}
        dt = time.time() - t0
        print(f"  → {r['outcome']} in {dt:.1f}s | skills_used={r['skills_used']} | py_verified={r['py_skill_verified']}")
        save_result(out_dir, i, tier, task, r)
        results.append((tier, task, r))
    return results


def explore(max_explore, target_repo, explore_file):
    explore_tasks = load_tasks(explore_file)[:max_explore]
    print(f"\n{'#'*70}\n# EXPLORATION: {len(explore_tasks)} warm-up tasks\n{'#'*70}")
    print(f"  Tasks file: {explore_file}")
    skills_before = set(os.listdir(SKILLS_PY)) if SKILLS_PY.is_dir() else set()
    for i, (_, task) in enumerate(explore_tasks, 1):
        print(f"\n[explore {i}/{len(explore_tasks)}] {task[:80]}")
        try:
            r = agent.run_single_task(task, target_repo=str(target_repo))
            print(f"  → {r['outcome']} | py_verified={r['py_skill_verified']}")
        except Exception as e:
            print(f"  ! errored: {e}")
    skills_after = set(os.listdir(SKILLS_PY)) if SKILLS_PY.is_dir() else set()
    new_skills = sorted(skills_after - skills_before)
    return len(new_skills), new_skills


def score_and_report(cold_results, warm_results, explore_count):
    print("\n>>> SCORING")
    sys.path.insert(0, str(HERE))
    import score
    summary_extra = {"skills_built_during_exploration": explore_count}
    score.score_all(
        cold_results, warm_results,
        summary_extra=summary_extra,
        out_path=str(RESULTS_DIR / "scores.json"),
    )
    print(f"\nDone. Scores at {RESULTS_DIR / 'scores.json'}")
    print(f"Run: venv/bin/python eval/report.py")


def main():
    parser = argparse.ArgumentParser(description="Run cold/warm experiment")
    parser.add_argument("--max-explore", type=int, default=20)
    parser.add_argument("--max-bench",   type=int, default=15)
    parser.add_argument("--model", default=None,
                        help="Override LLM model (overrides ANTHROPIC_MODEL env var)")
    parser.add_argument("--explore-tasks", default=None,
                        help="Path to exploration task file (overrides EXPLORE_TASKS_FILE env var)")
    parser.add_argument("--resume-warm", action="store_true",
                        help="Skip cold run and exploration — run warm benchmark only")
    parser.add_argument("--resume-cold", action="store_true",
                        help="Skip cold run — run exploration then warm benchmark")
    args = parser.parse_args()

    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com/apikey")
        sys.exit(1)
    if not TARGET_REPO.is_dir():
        print(f"ERROR: target repo missing at {TARGET_REPO}")
        print("Fix:  git clone --depth=1 https://github.com/tiangolo/fastapi.git eval/target_repo/fastapi")
        sys.exit(1)

    if args.model:
        agent.MODEL = args.model
        agent.budget = agent.TokenBudget(args.model)

    explore_file = args.explore_tasks or os.environ.get("EXPLORE_TASKS_FILE") or str(EXPLORE_FILE)
    if not Path(explore_file).exists():
        print(f"ERROR: exploration task file not found: {explore_file}")
        sys.exit(1)

    bench = load_tasks(BENCH_FILE)
    if args.max_bench < len(bench):
        by_tier = {}
        for t in bench:
            by_tier.setdefault(t[0], []).append(t)
        per_tier = max(1, args.max_bench // max(1, len(by_tier)))
        sliced = []
        for tier_tasks in by_tier.values():
            sliced.extend(tier_tasks[:per_tier])
        bench = sliced[:args.max_bench]
    print(f"Loaded {len(bench)} benchmark tasks (limit={args.max_bench})")
    print(f"Model: {agent.MODEL}")

    # ── RESUME WARM ── skip cold + exploration
    if args.resume_warm:
        print(f"\n[RESUME] Skipping cold run and exploration — running warm benchmark only")
        print(f"[RESUME] Skills in library: {count_skills()}")
        warm_results = run_condition("WARM", bench, WARM_DIR, TARGET_REPO)
        # Fake a zero cold run so scorer works
        cold_results = [(tier, task, {"outcome": "skip", "skills_used": [], "skills_considered": 0,
                                      "py_skill_verified": None, "py_skill_failed": False,
                                      "skill_composed": False, "composed_from": [],
                                      "code_executed": 0, "exec_results": []})
                        for tier, task in bench]
        score_and_report(cold_results, warm_results, count_skills())
        return

    # ── RESUME COLD ── skip cold, run exploration + warm
    if args.resume_cold:
        print(f"\n[RESUME] Skipping cold run — running exploration then warm")
        print("\n>>> RESETTING STATE FOR WARM CONDITION")
        reset_state()
        explore_count, explore_skills = explore(args.max_explore, TARGET_REPO, explore_file)
        print(f"\nExploration produced {explore_count} new verified py skills: {explore_skills}")
        warm_results = run_condition("WARM", bench, WARM_DIR, TARGET_REPO)
        cold_results = [(tier, task, {"outcome": "skip", "skills_used": [], "skills_considered": 0,
                                      "py_skill_verified": None, "py_skill_failed": False,
                                      "skill_composed": False, "composed_from": [],
                                      "code_executed": 0, "exec_results": []})
                        for tier, task in bench]
        score_and_report(cold_results, warm_results, explore_count)
        return

    # ── FULL RUN ──
    print("\n>>> RESETTING STATE FOR COLD CONDITION")
    reset_state()
    cold_results = run_condition("COLD", bench, COLD_DIR, TARGET_REPO)

    print("\n>>> RESETTING STATE FOR WARM CONDITION")
    reset_state()
    explore_count, explore_skills = explore(args.max_explore, TARGET_REPO, explore_file)
    print(f"\nExploration produced {explore_count} new verified py skills: {explore_skills}")
    warm_results = run_condition("WARM", bench, WARM_DIR, TARGET_REPO)

    score_and_report(cold_results, warm_results, explore_count)


if __name__ == "__main__":
    main()
