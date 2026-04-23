---
name: starlette_import_extractor
tags:
- starlette
- imports
- fastapi
trigger: when analyzing starlette imports in the fastapi repository
type: pattern
version: 1
success_count: 1
fail_count: 0
---
---
# Starlette Import Extractor
## Purpose
Extract starlette imports from python files in a directory and report which starlette names each one imports.

## When to use
Use this skill when analyzing starlette imports in the fastapi repository.

## How to use
1. Run the `extract_starlette_imports` function with the directory path as an argument.
2. The function will return a dictionary with file paths as keys and lists of starlette imports as values.
3. Use the output to identify areas where we can optimize or reduce the number of imports.