"""Cold vs Warm experiment for the self-constructing agent.

Run from the self_building_agent/ directory:
    venv/bin/python eval/run_experiment.py [--max-explore N]
"""
import os, sys, json, shutil, time
from datetime import datetime, timezone

# Make run.py importable
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import run as agent  # noqa

TARGET_REPO = os.path.join("eval", "target_repo", "fastapi")
BENCH_FILE = os.path.join("eval", "benchmark_tasks.txt")
EXPLORE_FILE = os.path.join("eval", "exploration_tasks.txt")
RESULTS_DIR = os.path.join("eval", "results")
COLD_DIR = os.path.join(RESULTS_DIR, "cold")
WARM_DIR = os.path.join(RESULTS_DIR, "warm")
BACKUP_DIR = os.path.join("eval", "backups")


def parse_arg(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def load_tasks(path):
    tasks = []
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "::" in line:
            tier, body = line.split("::", 1)
            tasks.append((tier.strip(), body.strip()))
        else:
            tasks.append(("UNTIERED", line))
    return tasks


def reset_state():
    """Wipe skills_py/ and memory/episodes.jsonl, backing up any existing state."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    if os.path.isdir("skills_py") and os.listdir("skills_py"):
        dst = os.path.join(BACKUP_DIR, f"skills_py_{stamp}")
        shutil.copytree("skills_py", dst)
    shutil.rmtree("skills_py", ignore_errors=True)
    os.makedirs("skills_py/archive", exist_ok=True)

    if os.path.exists("memory/episodes.jsonl"):
        shutil.copy("memory/episodes.jsonl", os.path.join(BACKUP_DIR, f"episodes_{stamp}.jsonl"))
        os.remove("memory/episodes.jsonl")
    os.makedirs("memory", exist_ok=True)

    # Reset agent's in-memory caches
    agent._episode_cache = None
    agent._repo_file_index_cache.clear()


def save_result(out_dir, idx, tier, task, result):
    os.makedirs(out_dir, exist_ok=True)
    payload = {
        "index": idx,
        "tier": tier,
        "task": task,
        **{k: v for k, v in result.items() if k != "exec_results"},
        "exec_results_count": len(result.get("exec_results") or []),
    }
    with open(os.path.join(out_dir, f"task_{idx:02d}.json"), "w") as f:
        json.dump(payload, f, indent=2, default=str)


def run_condition(label, tasks, out_dir, target_repo):
    print(f"\n{'#'*70}\n# {label}: {len(tasks)} benchmark tasks\n{'#'*70}")
    results = []
    for i, (tier, task) in enumerate(tasks, 1):
        print(f"\n[{label}] {i}/{len(tasks)} ({tier}) {task[:80]}")
        t0 = time.time()
        try:
            r = agent.run_single_task(task, target_repo=target_repo)
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


def explore(max_explore, target_repo):
    explore_tasks = load_tasks(EXPLORE_FILE)[:max_explore]
    print(f"\n{'#'*70}\n# EXPLORATION: {len(explore_tasks)} warm-up tasks\n{'#'*70}")
    skills_before = set(os.listdir("skills_py")) if os.path.isdir("skills_py") else set()
    for i, (_, task) in enumerate(explore_tasks, 1):
        print(f"\n[explore {i}/{len(explore_tasks)}] {task[:80]}")
        try:
            r = agent.run_single_task(task, target_repo=target_repo)
            print(f"  → {r['outcome']} | py_verified={r['py_skill_verified']}")
        except Exception as e:
            print(f"  ! errored: {e}")
    skills_after = set(os.listdir("skills_py")) if os.path.isdir("skills_py") else set()
    return len(skills_after - skills_before), sorted(skills_after - skills_before)


def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not set.")
        sys.exit(1)
    if not os.path.isdir(TARGET_REPO):
        print(f"ERROR: target repo missing at {TARGET_REPO}")
        sys.exit(1)

    max_explore = int(parse_arg("--max-explore", "20"))
    max_bench = int(parse_arg("--max-bench", "15"))
    bench = load_tasks(BENCH_FILE)
    if max_bench < len(bench):
        # Take a representative slice across tiers
        by_tier = {}
        for t in bench:
            by_tier.setdefault(t[0], []).append(t)
        per_tier = max(1, max_bench // max(1, len(by_tier)))
        sliced = []
        for tier_tasks in by_tier.values():
            sliced.extend(tier_tasks[:per_tier])
        bench = sliced[:max_bench]
    print(f"Loaded {len(bench)} benchmark tasks (limit={max_bench})")

    # ----- COLD -----
    print("\n>>> RESETTING STATE FOR COLD CONDITION")
    reset_state()
    cold_results = run_condition("COLD", bench, COLD_DIR, TARGET_REPO)

    # ----- WARM (reset, then explore, then bench) -----
    print("\n>>> RESETTING STATE FOR WARM CONDITION")
    reset_state()
    explore_count, explore_skills = explore(max_explore, TARGET_REPO)
    print(f"\nExploration produced {explore_count} new verified py skills: {explore_skills}")
    warm_results = run_condition("WARM", bench, WARM_DIR, TARGET_REPO)

    # ----- Score -----
    print("\n>>> SCORING")
    import score
    summary_extra = {
        "skills_built_during_exploration": explore_count,
    }
    score.score_all(cold_results, warm_results, summary_extra=summary_extra,
                    out_path=os.path.join(RESULTS_DIR, "scores.json"))
    print(f"\nDone. Scores at {os.path.join(RESULTS_DIR, 'scores.json')}")
    print("Run: venv/bin/python eval/report.py")


if __name__ == "__main__":
    main()
