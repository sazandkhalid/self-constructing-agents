"""Print a human-readable experiment report.

Usage:
    venv/bin/python eval/report.py              # fastapi experiment
    venv/bin/python eval/report.py --payment    # payment rail experiment
"""
import argparse, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
sys.path.insert(0, ROOT)

SCORES         = "eval/results/scores.json"
SCORES_PAYMENT = "eval/scores_payment.json"


def _verdict(prompt):
    try:
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        r = client.chat.completions.create(
            model="qwen/qwen3-32b",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"(LLM verdict unavailable: {e})"


def report_payment(data):
    s = data["summary"]
    cold = data.get("cold", [])
    warm = data.get("warm", [])

    print("=" * 60)
    print("=== PAYMENT RAIL EXPERIMENT RESULTS ===")
    print(f"Target repo: ISO 20022 / ACH synthetic codebase")
    cfg = data.get("config", {})
    print(f"Tasks: {cfg.get('max_bench','?')} benchmark  |  {cfg.get('max_explore','?')} exploration")
    print()
    print(f"COLD (no skills):     avg score {s['cold_avg']:.2f}/3.0")
    print(f"WARM (with skills):   avg score {s['warm_avg']:.2f}/3.0")
    print(f"Improvement:          {s['improvement_pct']:+.1f}%")
    print()
    cb, wb = s.get("cold_by_tier", {}), s.get("warm_by_tier", {})
    tier_labels = [("TIER1","structural"), ("TIER2","translation"), ("TIER3","synthesis ")]
    for tier, label in tier_labels:
        c = cb.get(tier, 0.0)
        w = wb.get(tier, 0.0)
        print(f"Tier {tier[-1]} ({label}):  cold {c:.2f} → warm {w:.2f}  (Δ {w-c:+.2f})")
    print()
    print(f"Skills built during exploration: {s.get('skills_built_during_exploration','?')}")
    print(f"Skills used in warm condition:   {s.get('skills_used_in_warm','?')}")
    print(f"Skill compositions:              {s.get('compositions','?')}")
    print()
    print(f"ComplianceShield results:")
    print(f"  PASS:  {s.get('compliance_pass',0)}")
    print(f"  WARN:  {s.get('compliance_warn',0)}")
    print(f"  BLOCK: {s.get('compliance_block',0)}")
    print()

    # Top skills in warm run
    skill_contrib = {}
    for entry in warm:
        sk = entry.get("py_skill_verified")
        if sk:
            skill_contrib.setdefault(sk, []).append(entry["score"])
    if skill_contrib:
        print("Top performing skills (warm run):")
        ranked = sorted(skill_contrib.items(), key=lambda kv: -sum(kv[1])/len(kv[1]))
        for i, (name, scores) in enumerate(ranked[:5], 1):
            print(f"  {i}. {name} (used {len(scores)} times, avg {sum(scores)/len(scores):.2f})")
        print()

    # Failure type distribution
    for label, entries in [("cold", cold), ("warm", warm)]:
        d = {}
        for e in entries:
            ft = e.get("failure_type")
            if ft:
                d[ft] = d.get(ft, 0) + 1
        if d:
            print(f"Failure type distribution ({label}):")
            for ft, n in sorted(d.items(), key=lambda x: -x[1]):
                print(f"  {ft}: {n}")
            attempts = [e for e in entries if e.get("recovery_attempted")]
            if attempts:
                succ = sum(1 for e in attempts if e.get("recovery_succeeded"))
                print(f"  Recovery success rate: {succ/len(attempts)*100:.0f}% ({len(attempts)} attempts)")
            print()

    # LLM verdict
    verdict_prompt = (
        f"You are reviewing the results of a cold/warm experiment testing whether a "
        f"self-constructing agent performs better on financial protocol integration tasks "
        f"when it has a pre-built skill library. "
        f"Cold avg score: {s['cold_avg']:.2f}. Warm avg score: {s['warm_avg']:.2f}. "
        f"Delta: {s['warm_avg']-s['cold_avg']:+.2f}. "
        f"Tier 1 delta (structural): {s['tier1_delta']:+.2f}. "
        f"Tier 2 delta (translation): {s['tier2_delta']:+.2f}. "
        f"Tier 3 delta (synthesis): {s['tier3_delta']:+.2f}. "
        f"Total skills verified in warm run: {s.get('skills_used_in_warm',0)}. "
        f"Skills that hit ComplianceShield WARN: {s.get('compliance_warn',0)}. "
        f"Write a two-sentence verdict: does accumulated protocol knowledge help, "
        f"and which tier shows the strongest signal?"
    )
    print("=== VERDICT ===")
    print(_verdict(verdict_prompt))
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--payment", action="store_true", help="Show payment rail experiment report")
    args = parser.parse_args()

    if args.payment:
        if not os.path.exists(SCORES_PAYMENT):
            print(f"No payment scores at {SCORES_PAYMENT}. Run eval/run_payment_experiment.py first.")
            sys.exit(1)
        data = json.load(open(SCORES_PAYMENT))
        report_payment(data)
        return
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
            model="qwen/qwen3-32b",
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
