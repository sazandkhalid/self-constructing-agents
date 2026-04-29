#!/usr/bin/env python3
"""
ask.py — Single-task interactive entry point for the Self-Constructing Agent.

Usage:
    python ask.py "fetch the current price of AAPL and compute its 5-day moving average"
    python ask.py "fetch the current temperature in San Francisco"
    python ask.py "validate this IBAN: GB82WEST12345698765432"

The script loads the existing agent infrastructure, appends the capability-
discovery addendum to the system prompt, runs the task, then pretty-prints a
summary reconstructed from structured logs.
"""

import json
import os
import sys
from pathlib import Path

# ── Resolve project root regardless of CWD ──────────────────────────────────
ROOT = Path(__file__).parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

# ── ANSI colour helpers ──────────────────────────────────────────────────────
_RESET  = "\033[0m"
_CYAN   = "\033[36m"
_GREEN  = "\033[32m"
_RED    = "\033[31m"
_YELLOW = "\033[33m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"

def _c(text, *codes): return "".join(codes) + text + _RESET
def cyan(t):   return _c(t, _CYAN)
def green(t):  return _c(t, _GREEN)
def red(t):    return _c(t, _RED)
def yellow(t): return _c(t, _YELLOW)
def bold(t):   return _c(t, _BOLD)
def dim(t):    return _c(t, _DIM)

WIDTH = 57

def box_top(title=""):
    inner = f"  {title:<{WIDTH - 4}}" if title else " " * (WIDTH - 2)
    return f"╭{'─' * (WIDTH - 2)}╮\n│{inner}│\n╰{'─' * (WIDTH - 2)}╯"

def box_section(title, rows):
    """Render a two-column summary box."""
    lines = [f"╭{'─' * (WIDTH - 2)}╮", f"│  {bold(title):<{WIDTH + 7}}│",
             f"├{'─' * (WIDTH - 2)}┤"]
    for k, v in rows:
        cell = f"  {cyan(k + ':')} {v}"
        # pad to WIDTH-2 visible chars (rough)
        lines.append(f"│{cell:<{WIDTH + 6}}│")
    lines.append(f"╰{'─' * (WIDTH - 2)}╯")
    return "\n".join(lines)


# ── Read structured log tail to reconstruct gate output ─────────────────────
def _tail_log(log_path: Path, n: int = 200) -> list[dict]:
    if not log_path.exists():
        return []
    entries = []
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries[-n:]


def _gate_symbol(passed: bool) -> str:
    return green("✓ PASS") if passed else red("✗ FAIL")


def _render_tool_authoring(entries: list[dict], run_start_ts: str) -> list[str]:
    """Reconstruct per-tool gate output from log entries written during this run."""
    lines = []
    seen = {}  # tool_name -> list of attempt dicts
    for e in entries:
        if e.get("timestamp", "") < run_start_ts:
            continue
        outcome = e.get("outcome", "")
        name = e.get("tool_name")
        if not name:
            continue
        if outcome in ("tool_verified", "tool_verify_failed", "tool_retry"):
            seen.setdefault(name, []).append(e)

    for name, evts in seen.items():
        for e in evts:
            attempt = e.get("tool_attempt", 1)
            outcome = e.get("outcome", "")
            if outcome == "tool_verified":
                lines.append(f"\n  {cyan('[tool authoring]')} {bold(name)} (attempt {attempt}/3)")
                lines.append(f"  ├─ Gate 1 (AST validity)        {green('✓ PASS')}")
                lines.append(f"  ├─ Gate 2 (subprocess test)     {green('✓ PASS')}  (stdout: \"TEST PASSED\")")
                lines.append(f"  ├─ Gate 3 (schema validation)   {green('✓ PASS')}")
                lines.append(f"  └─ Gate 4 (ComplianceShield)    {green('✓ PASS')}")
                lines.append(f"  {green('→ Registered:')} tools/registry.json")
            elif outcome == "tool_verify_failed":
                gate  = e.get("tool_gate", "unknown gate")
                error = e.get("tool_error", "")[:120]
                lines.append(f"\n  {cyan('[tool authoring]')} {bold(name)} (attempt {attempt}/3)")
                lines.append(f"  {red('✗')} Gate '{gate}' failed: {error}")
                if attempt < 3:
                    lines.append(f"  {yellow('→ Retrying...')}")
    return lines


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python ask.py \"<task>\"")
        sys.exit(1)

    task = " ".join(sys.argv[1:])

    # Load addendum
    addendum_path = ROOT / "prompts" / "interactive_task_addendum.txt"
    addendum = addendum_path.read_text() if addendum_path.exists() else ""

    # Print header
    print(f"\n{box_top('Self-Constructing Agent · Single Task')}")
    print(f"\n  {cyan('[task]')} {task}\n")

    # Load env if .env exists (for standalone invocation)
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    # Record log size before run so we only read new entries afterwards
    log_path = ROOT / "logs" / "log.jsonl"
    log_size_before = log_path.stat().st_size if log_path.exists() else 0

    # Import agent (after env is loaded)
    print(f"  {dim('[loading agent infrastructure...]')}")
    import run as agent
    from datetime import datetime, timezone
    run_start_ts = datetime.now(timezone.utc).isoformat()

    # Run
    print(f"  {cyan('[reasoning]')} Checking existing capabilities...\n")
    result = agent.run_single_task(
        task,
        system_prompt_addendum=addendum,
    )

    # Read new log entries written during this run
    new_entries = []
    if log_path.exists():
        raw = log_path.read_bytes()[log_size_before:]
        for line in raw.decode(errors="replace").splitlines():
            line = line.strip()
            if line:
                try:
                    new_entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # Render tool-authoring gates from structured log
    gate_lines = _render_tool_authoring(new_entries, run_start_ts)
    if gate_lines:
        for l in gate_lines:
            print(l)
        print()

    # Print tool execution results from log (these fire even if final LLM call fails)
    for e in new_entries:
        if e.get("outcome") == "tool_verified":
            name = e.get("tool_name", "?")
            print(f"  {cyan('[tool call]')} {name}(...)")
        if e.get("outcome") == "tool_results":
            for tname, tresult in e.get("tool_results", {}).items():
                print(f"\n  {cyan('[tool result:')} {tname}{cyan(']')}")
                for line in tresult.strip().splitlines():
                    print(f"    {line}")

    # Print the agent's answer
    response = result.get("response", "")
    if response:
        print(f"\n  {cyan('[answer]')}")
        for line in response.strip().splitlines():
            print(f"  {line}")
    elif not any(e.get("outcome") == "tool_results" for e in new_entries):
        print(f"\n  {yellow('[no answer returned — model may have hit rate limit]')}")

    # Tally tools authored this run
    tools_authored = [e["tool_name"] for e in new_entries if e.get("outcome") == "tool_verified"]
    tools_failed   = [e["tool_name"] for e in new_entries if e.get("outcome") == "tool_verify_failed"
                      and e.get("tool_attempt", 1) == 3]  # only final failures

    skill_name = result.get("py_skill_verified")
    outcome    = result.get("outcome", "fail")
    status_str = green("SUCCESS") if outcome == "success" else red("FAIL")

    tools_str = f"{len(tools_authored)}" + (f" ({', '.join(tools_authored)})" if tools_authored else "")
    skill_str = skill_name if skill_name else "0"

    print(f"\n{box_section('Summary', [('Tools authored this run', tools_str), ('Skills authored this run', skill_str), ('Status', status_str)])}\n")

    sys.exit(0 if outcome == "success" else 1)


if __name__ == "__main__":
    main()
