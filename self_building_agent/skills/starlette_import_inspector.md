---
name: starlette_import_inspector
tags:
- starlette
- import inspection
trigger: when investigating starlette imports in a FastAPI project
type: pattern
version: 1
success_count: 2
fail_count: 0
---
---
# Starlette Import Inspector
## Purpose
Inspect Python code to understand how starlette imports are used.

## When to use
Use this skill when working with FastAPI projects and need to investigate how starlette imports are used in specific modules.

## How to use
1. Identify the module to inspect.
2. Use the `ast` module to parse the Python file.
3. Extract import statements and identify imports from the starlette module.
4. Analyze the code to understand how the starlette imports are used.