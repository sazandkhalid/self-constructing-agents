"""Print a human-readable experiment report from eval/results/scores.json."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
sys.path.insert(0, ROOT)

SCORES = "eval/results/scores.json"

def main():
    if not os.path.exists(SCORES):
        print(f"No scores file at {SCORES}. Run eval/run_experiment.py first.")
        sys.exit(1)
    data = json.load(open(SCORES))
    s = data["summary"]
    cold = data["cold"]
    warm = data["warm"]

    print("=" * 60)
    print("=== EXPERIMENT RESULTS ===")
    print("Target repo: fastapi")
    print(f"Tasks: {len(cold)} (5 structural / 5 pattern / 5 novel)")
    print()
    print(f"COLD (no skills):     avg score {s['cold_avg']:.2f}/3.0")
    print(f"WARM (with skills):   avg score {s['warm_avg']:.2f}/3.0")
    print(f"Improvement:          {s['improvement_pct']:+.1f}%")
    print()
    cb = s.get("cold_by_tier", {})
    wb = s.get("warm_by_tier", {})
    for tier, label in [("TIER1", "structural"), ("TIER2", "pattern"), ("TIER3", "novel  ")]:
        c = cb.get(tier, 0.0)
        w = wb.get(tier, 0.0)
        print(f"Tier {tier[-1]} ({label}):  cold {c:.2f} → warm {w:.2f}  (Δ {w-c:+.2f})")
    print()
    print(f"Skills built during exploration: {s.get('skills_built_during_exploration', '?')}")
    print(f"Skills used in warm condition:   {s['skills_used_in_warm']}")
    print(f"Skill compositions:              {s['compositions']}")
    print()

    # Failure type distribution
    def dist(entries):
        d = {}
        for e in entries:
            ft = e.get("failure_type")
            if ft:
                d[ft] = d.get(ft, 0) + 1
        return d

    def recovery_rate(entries):
        attempts = [e for e in entries if e.get("recovery_attempted")]
        if not attempts:
            return None, 0
        succ = sum(1 for e in attempts if e.get("recovery_succeeded"))
        return succ / len(attempts) * 100, len(attempts)

    for label, entries in [("cold", cold), ("warm", warm)]:
        d = dist(entries)
        if d:
            print(f"Failure type distribution ({label}):")
            for ft, n in sorted(d.items(), key=lambda x: -x[1]):
                print(f"  {ft}: {n}")
            rr, n = recovery_rate(entries)
            if rr is not None:
                print(f"  Recovery success rate: {rr:.0f}% ({n} attempts)")
            print()

    # Top performing skills (skills that appear in successful warm tasks)
    skill_contrib = {}
    for entry in warm:
        sk = entry.get("py_skill_verified")
        if sk:
            skill_contrib.setdefault(sk, []).append(entry["score"])
    if skill_contrib:
        print("Top performing skills:")
        ranked = sorted(skill_contrib.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))
        for i, (name, scores) in enumerate(ranked[:5], 1):
            print(f"  {i}. {name} (used {len(scores)} times, avg score {sum(scores)/len(scores):.2f})")
        print()

    # LLM verdict
    try:
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        prompt = f"""You are interpreting an experiment that compares a programming agent
with vs. without an accumulated skill library.

Results:
- COLD avg score: {s['cold_avg']:.2f}/3.0
- WARM avg score: {s['warm_avg']:.2f}/3.0
- Improvement: {s['improvement_pct']:+.1f}%
- Tier deltas: structural {s['tier1_delta']:+.2f}, pattern {s['tier2_delta']:+.2f}, novel {s['tier3_delta']:+.2f}
- Skills built during exploration: {s.get('skills_built_during_exploration', 0)}
- Skills used in warm: {s['skills_used_in_warm']}
- Compositions: {s['compositions']}

Write a single paragraph (4-6 sentences) interpreting whether the hypothesis
"an agent with an accumulated repo-specific skill library performs measurably
better than one without" is supported by these numbers. Be honest about
weak or null results."""
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        verdict = r.choices[0].message.content.strip()
    except Exception as e:
        verdict = f"(LLM verdict unavailable: {e})"

    print("=== VERDICT ===")
    print(verdict)
    print("=" * 60)

if __name__ == "__main__":
    main()
