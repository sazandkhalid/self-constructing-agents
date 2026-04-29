"""
MCP (Model Context Protocol) tool calling layer.

Provides 4 builtin tools and supports agent-built tool registration.
Tool registry is persisted to tools/registry.json.

Builtin tools
─────────────
  read_file(path)       — read a local file (up to 4 000 chars)
  search_code(query)    — keyword search across .py files in the working tree
  run_python(code)      — execute a Python snippet in a subprocess
  list_skills()         — list all verified skills from skills_py/index.json

Agent-built tools are registered via ---MCP TOOL--- blocks emitted in LLM
responses and stored in tools/registry.json under "agent_built".

Tool call format (in LLM responses):
─────────────────────────────────────
---TOOL CALL---
{"tool": "read_file", "args": {"path": "skills_py/index.json"}}
---END TOOL CALL---

Tool registration format:
─────────────────────────
---MCP TOOL---
{"name": "my_tool", "description": "does X", "args": ["input"], "code": "print({{input}})"}
---END MCP TOOL---
"""

import json
import os
import re
import subprocess
import tempfile

TOOLS_DIR = "tools"
REGISTRY_PATH = os.path.join(TOOLS_DIR, "registry.json")

os.makedirs(TOOLS_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# Registry helpers
# ─────────────────────────────────────────────────────────────

def _load_registry() -> dict:
    if os.path.exists(REGISTRY_PATH):
        try:
            return json.load(open(REGISTRY_PATH))
        except Exception:
            pass
    return {"agent_built": []}


def _save_registry(registry: dict):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)


# ─────────────────────────────────────────────────────────────
# Builtin tool implementations
# ─────────────────────────────────────────────────────────────

def _tool_read_file(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()[:4000]
    except Exception as e:
        return f"ERROR reading {path}: {e}"


def _tool_search_code(query: str, root: str = ".") -> str:
    results = []
    q = query.lower()
    skip_dirs = {"venv", "__pycache__", ".git", "archive", "node_modules", ".mypy_cache"}
    for dirpath, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            try:
                text = open(full).read()
                if q in text.lower():
                    for i, line in enumerate(text.splitlines(), 1):
                        if q in line.lower():
                            results.append(f"{full}:{i}: {line.strip()}")
            except OSError:
                pass
            if len(results) >= 20:
                break
        if len(results) >= 20:
            break
    return "\n".join(results[:20]) if results else "no matches found"


def _tool_run_python(code: str) -> str:
    try:
        import ast as _ast
        _ast.parse(code)
    except SyntaxError as e:
        return f"SYNTAX ERROR: {e}"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        r = subprocess.run(["python3", path], capture_output=True, text=True, timeout=15)
        out = r.stdout or ""
        if r.stderr:
            out += "\nSTDERR:\n" + r.stderr
        return out[:2000]
    except subprocess.TimeoutExpired:
        return "TIMEOUT after 15s"
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _tool_list_skills() -> str:
    idx_path = "skills_py/index.json"
    if not os.path.exists(idx_path):
        return "no skills found (index.json missing)"
    try:
        skills = json.load(open(idx_path))
        if not skills:
            return "no verified skills yet"
        lines = [
            f"- {s.get('skill', s.get('file', '?'))} "
            f"(v{s.get('version', 1)}, tags: {', '.join(s.get('tags', []))})"
            for s in skills
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"ERROR reading index: {e}"


BUILTIN_TOOLS: dict[str, dict] = {
    "read_file": {
        "fn": _tool_read_file,
        "args": ["path"],
        "description": "Read a local file. Returns up to 4000 chars.",
    },
    "search_code": {
        "fn": _tool_search_code,
        "args": ["query"],
        "description": "Search .py files for a keyword. Returns matching lines.",
    },
    "run_python": {
        "fn": _tool_run_python,
        "args": ["code"],
        "description": "Execute a Python snippet in a subprocess. Returns stdout/stderr.",
    },
    "list_skills": {
        "fn": _tool_list_skills,
        "args": [],
        "description": "List all verified skills in skills_py/.",
    },
}


# ─────────────────────────────────────────────────────────────
# Tool call parsing and dispatch
# ─────────────────────────────────────────────────────────────

def parse_tool_calls(response_text: str) -> list[dict]:
    """Extract all ---TOOL CALL--- blocks from an LLM response."""
    calls = []
    if "---TOOL CALL---" not in response_text:
        return calls
    blocks = response_text.split("---TOOL CALL---")[1:]
    for block in blocks:
        body = block.split("---END TOOL CALL---")[0].strip()
        try:
            call = json.loads(body)
            if isinstance(call, dict) and "tool" in call:
                calls.append(call)
                continue
        except json.JSONDecodeError:
            pass
        # Fallback: key: value line parsing
        call = {}
        for line in body.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                call[k.strip()] = v.strip()
        if "tool" in call:
            calls.append(call)
    return calls


def dispatch_tool(call: dict) -> str:
    """Execute a parsed tool call and return a string result."""
    tool_name = call.get("tool", "")
    raw_args = call.get("args", {})

    # Normalise args: accept {"path": "..."} or plain string shorthand
    if isinstance(raw_args, str):
        arg_names = BUILTIN_TOOLS.get(tool_name, {}).get("args", ["input"])
        args = {arg_names[0]: raw_args} if arg_names else {}
    else:
        args = raw_args if isinstance(raw_args, dict) else {}

    if tool_name in BUILTIN_TOOLS:
        fn = BUILTIN_TOOLS[tool_name]["fn"]
        arg_names = BUILTIN_TOOLS[tool_name]["args"]
        positional = [args.get(a, "") for a in arg_names]
        try:
            return fn(*positional) if positional else fn()
        except Exception as e:
            return f"tool error in {tool_name}: {e}"

    # Check agent-built tools
    registry = _load_registry()
    for t in registry.get("agent_built", []):
        if t.get("name") == tool_name:
            code = t.get("code", "")
            if code:
                return _dispatch_agent_tool(tool_name, code, args)
    return f"unknown tool: {tool_name!r}"


def _dispatch_agent_tool(tool_name: str, code: str, args: dict) -> str:
    """Execute an agent-built tool by calling its function with actual arguments.

    Strips the __main__ test block from the registered code, then generates a
    wrapper that calls the function with the provided args and JSON-serialises
    the result.  This replaces the old approach of running the whole file as a
    script (which executed the __main__ test block instead of the function).
    """
    # Strip everything from `if __name__ == "__main__":` onwards
    body_lines = []
    for line in code.splitlines():
        if line.strip().startswith("if __name__") and "__main__" in line:
            break
        body_lines.append(line)
    body = "\n".join(body_lines)

    # Build keyword args repr safely
    args_repr = ", ".join(f"{k}={repr(v)}" for k, v in args.items())

    wrapper = f"""{body}

import json as _json, sys as _sys
try:
    _result = {tool_name}({args_repr})
    print(_json.dumps(_result) if not isinstance(_result, str) else _result)
except Exception as _e:
    print(_json.dumps({{"error": str(_e)}}))
    _sys.exit(1)
"""
    return _tool_run_python(wrapper)


def execute_tool_calls(response_text: str) -> list[dict]:
    """Find, dispatch, and collect results for all tool calls in a response."""
    results = []
    for call in parse_tool_calls(response_text):
        result = dispatch_tool(call)
        results.append({"call": call, "result": result})
    return results


# ─────────────────────────────────────────────────────────────
# Agent-built tool registration
# ─────────────────────────────────────────────────────────────

def parse_mcp_tool_blocks(response_text: str) -> list[dict]:
    """Extract ---MCP TOOL--- registration blocks from LLM responses.

    The LLM emits blocks in YAML format with a multi-line `code` field using
    the block scalar style (code: |). The old line-by-line fallback captured
    only `|` as the code value, causing every tool to fail AST Gate 1.
    Now tries JSON → YAML → line-by-line in that order.
    """
    import yaml as _yaml
    tools = []
    if "---MCP TOOL---" not in response_text:
        return tools
    blocks = response_text.split("---MCP TOOL---")[1:]
    for block in blocks:
        body = block.split("---END MCP TOOL---")[0].strip()
        t = None
        # 1. Try JSON (agent may emit JSON-formatted blocks)
        try:
            t = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            pass
        # 2. Try YAML — handles multi-line code: | block scalars correctly
        if t is None:
            try:
                t = _yaml.safe_load(body)
                if not isinstance(t, dict):
                    t = None
            except Exception:
                t = None
        # 3. Last resort: naive key: value (only captures single-line values)
        if t is None:
            t = {}
            for line in body.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    t[k.strip()] = v.strip()
        if t and t.get("name") and t.get("code"):
            tools.append(t)
    return tools


def _verify_tool(tool: dict) -> tuple[bool, str, str]:
    """Run the four-gate verification pipeline on an agent-authored tool.

    # TODO: factor shared verification primitive between skills and tools
    # Duplication of gate logic is intentional for demo timeline. Future pass
    # should extract ast_gate(), subprocess_gate(), compliance_gate() as
    # standalone callables shared by both materialize_py_skill() and here.

    Gates:
      1. AST validity      — code must parse without SyntaxError
      2. Subprocess test   — code must execute and print "TEST PASSED"
      3. Schema validity   — input_schema and output_schema must be present
                             and each key must have a non-empty "description"
      4. ComplianceShield  — must not be BLOCK

    Returns (passed: bool, gate_name: str, error_message: str).
    gate_name is empty string on full pass.
    """
    import ast as _ast
    import sys as _sys

    code = tool.get("code", "")
    name = tool.get("name", "?")

    # ── Gate 1: AST validity ────────────────────────────────────
    try:
        _ast.parse(code)
    except SyntaxError as e:
        return False, "AST validity", f"SyntaxError: {e}"

    # ── Gate 2: subprocess test ─────────────────────────────────
    import tempfile, subprocess as _sp, os as _os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        _path = f.name
    try:
        result = _sp.run(
            [_sys.executable, _path],
            capture_output=True, text=True, timeout=30,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        if result.returncode != 0 or "TEST PASSED" not in stdout:
            reason = stderr.strip()[:300] if stderr else f"no TEST PASSED in stdout: {stdout[:200]}"
            return False, "subprocess test", reason
    except _sp.TimeoutExpired:
        return False, "subprocess test", f"timeout after 30s"
    finally:
        try:
            _os.unlink(_path)
        except OSError:
            pass

    # ── Gate 3: schema validity ─────────────────────────────────
    for schema_key in ("input_schema", "output_schema"):
        schema = tool.get(schema_key)
        if not isinstance(schema, dict) or not schema:
            return False, "schema validity", (
                f"'{schema_key}' is missing or empty. "
                "Tool blocks must include both input_schema and output_schema "
                "as dicts where each key has a non-empty 'description' field."
            )
        for field_name, field_def in schema.items():
            if not isinstance(field_def, dict):
                return False, "schema validity", (
                    f"'{schema_key}.{field_name}' must be a dict with a 'description' key."
                )
            if not field_def.get("description", "").strip():
                return False, "schema validity", (
                    f"'{schema_key}.{field_name}.description' is missing or empty."
                )

    # ── Gate 4: ComplianceShield ────────────────────────────────
    try:
        from compliance import check as _shield_check, ShieldOutcome
        metadata = {"skill": name, "audit_required": False}
        result = _shield_check(code, metadata)
        if result.outcome == ShieldOutcome.BLOCK:
            return False, "ComplianceShield", result.reason
        # WARN is allowed — tool registers with a flag
    except ImportError:
        pass  # compliance module not available — skip gate 4

    return True, "", ""


def register_agent_tools(response_text: str) -> dict:
    """Parse, verify (four gates), and persist agent-built tools.

    Returns:
        {
          "registered": list[str],   # names that passed all gates
          "failed":     list[dict],  # {name, gate, error} for each rejection
        }
    """
    new_tools = parse_mcp_tool_blocks(response_text)
    if not new_tools:
        return {"registered": [], "failed": []}

    registry = _load_registry()
    existing_names = {t["name"] for t in registry.get("agent_built", [])}
    registered = []
    failed = []

    for t in new_tools:
        name = t.get("name", "?")
        if name in existing_names:
            continue  # already registered — skip silently

        passed, gate, error = _verify_tool(t)
        if not passed:
            failed.append({"name": name, "gate": gate, "error": error})
            continue

        registry.setdefault("agent_built", []).append(t)
        registered.append(name)

    if registered:
        _save_registry(registry)

    return {"registered": registered, "failed": failed}


# ─────────────────────────────────────────────────────────────
# Prompt injection helper
# ─────────────────────────────────────────────────────────────

def tool_manifest_for_prompt() -> str:
    """Return a formatted tool manifest for injecting into the system prompt."""
    lines = ["Available MCP tools (invoke via ---TOOL CALL--- blocks):"]
    for name, info in BUILTIN_TOOLS.items():
        args_str = ", ".join(info["args"]) if info["args"] else "(no args)"
        lines.append(f"  {name}({args_str}) — {info['description']}")
    registry = _load_registry()
    for t in registry.get("agent_built", []):
        lines.append(f"  {t['name']}({', '.join(t.get('args', []))}) — {t.get('description', 'agent-built tool')}")
    lines += [
        "",
        "Tool call format:",
        "---TOOL CALL---",
        '{"tool": "read_file", "args": {"path": "skills_py/index.json"}}',
        "---END TOOL CALL---",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    r = dispatch_tool({"tool": "list_skills", "args": {}})
    print(f"list_skills: {r[:100]}")
    r = dispatch_tool({"tool": "run_python", "args": {"code": "print('hello from mcp')"}})
    assert "hello from mcp" in r, f"unexpected output: {r}"
    r = dispatch_tool({"tool": "search_code", "args": {"query": "def run_single_task"}})
    print(f"search_code result: {r[:100]}")
    print("TEST PASSED")
