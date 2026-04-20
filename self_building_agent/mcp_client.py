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
                first_val = str(list(args.values())[0]) if args else ""
                return _tool_run_python(code.replace("{{input}}", first_val))
    return f"unknown tool: {tool_name!r}"


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
    """Extract ---MCP TOOL--- registration blocks from LLM responses."""
    tools = []
    if "---MCP TOOL---" not in response_text:
        return tools
    blocks = response_text.split("---MCP TOOL---")[1:]
    for block in blocks:
        body = block.split("---END MCP TOOL---")[0].strip()
        try:
            t = json.loads(body)
        except json.JSONDecodeError:
            t = {}
            for line in body.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    t[k.strip()] = v.strip()
        if t.get("name") and t.get("code"):
            tools.append(t)
    return tools


def register_agent_tools(response_text: str) -> list[str]:
    """Parse and persist any agent-built tools. Returns list of newly registered names."""
    new_tools = parse_mcp_tool_blocks(response_text)
    if not new_tools:
        return []
    registry = _load_registry()
    existing_names = {t["name"] for t in registry.get("agent_built", [])}
    registered = []
    for t in new_tools:
        if t["name"] not in existing_names:
            registry.setdefault("agent_built", []).append(t)
            registered.append(t["name"])
    if registered:
        _save_registry(registry)
    return registered


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
