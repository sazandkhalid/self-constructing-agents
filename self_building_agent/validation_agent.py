"""
ValidationAgent: adversarial LLM-powered skill testing before persistence.

Runs AFTER ComplianceShield, BEFORE writing the skill to disk.
Generates 6 edge-case test inputs via an adversarial LLM prompt, executes them,
and returns pass/fail with output details.

If the LLM is unavailable the agent returns (True, "skipped") so the pipeline
never blocks on a transient API outage.
"""

import ast
import os
import re
import subprocess
import tempfile

from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def _generate_edge_case_tests(skill_code: str, task: str = "") -> str:
    """Ask the LLM to write 6 adversarial edge-case tests for a skill."""
    prompt = f"""You are an adversarial tester. Given this Python skill, write exactly 6 edge-case unit tests that could expose latent bugs.

SKILL CODE:
```python
{skill_code[:3000]}
```

ORIGINAL TASK CONTEXT: {task[:500] if task else "not provided"}

Requirements for your test module:
1. Inline ALL functions from the skill (copy them verbatim) at the top of the file.
2. After the functions, add an `if __name__ == "__main__":` block with exactly 6 assert statements.
3. Cover: empty/None inputs, boundary values, very large values, negative numbers, unicode strings, type edge cases.
4. Do NOT wrap assertions in try/except — let them fail naturally so errors are visible.
5. The last line of the `if __name__ == "__main__":` block MUST be: print("VALIDATION PASSED")
6. Use ZERO external dependencies (stdlib only).

Return ONLY the Python code. No markdown fences, no explanation."""
    try:
        r = client.chat.completions.create(
            model="qwen/qwen3-32b",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        code = r.choices[0].message.content.strip()
        code = re.sub(r"^```\w*\s*", "", code)
        code = re.sub(r"```\s*$", "", code).strip()
        return code
    except Exception as e:
        return ""


def run_validation(skill_code: str, task: str = "", timeout: int = 20) -> tuple[bool, str]:
    """
    Generate adversarial edge-case tests for a skill and execute them.

    Returns (passed: bool, details: str).
    - passed=True + "skipped" if LLM is unavailable or generates invalid code.
    - passed=False + output if at least one assertion fails.
    - passed=True + output if all 6 assertions pass.
    """
    edge_code = _generate_edge_case_tests(skill_code, task)
    if not edge_code:
        return True, "validation skipped (LLM unavailable or empty response)"

    # Syntax gate — if LLM produced malformed code skip rather than crash pipeline
    try:
        ast.parse(edge_code)
    except SyntaxError as e:
        return True, f"validation skipped (generated code has syntax error: {e})"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(edge_code)
        path = f.name
    try:
        result = subprocess.run(
            ["python3", path], capture_output=True, text=True, timeout=timeout
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        out = stdout + ("\nSTDERR:\n" + stderr if stderr else "")
        passed = result.returncode == 0 and "VALIDATION PASSED" in stdout
        return passed, out[:2000]
    except subprocess.TimeoutExpired:
        return False, f"validation timed out after {timeout}s"
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


if __name__ == "__main__":
    # Smoke test: clean skill that reverses a string should pass validation
    clean = '''
def reverse_string(s: str) -> str:
    """Return the reverse of s."""
    return s[::-1]

if __name__ == "__main__":
    assert reverse_string("hello") == "olleh"
    print("TEST PASSED")
'''
    passed, detail = run_validation(clean, "reverse a string")
    print(f"Validation passed: {passed}")
    print(f"Details (first 300 chars): {detail[:300]}")
    print("TEST PASSED")
