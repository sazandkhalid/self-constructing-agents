---
name: python_import_analyzer
tags:
- python
- import
- analysis
trigger: when analyzing Python code for imports from specific modules
type: pattern
version: 1
success_count: 24
fail_count: 6
---
---
# Python Import Analyzer
## Purpose
Analyze Python code to identify imports from specific modules.

## When to use
Use this skill when you need to traverse a directory, inspect Python files, and extract imports from specific modules.

## How to use
1. Define the directory to scan.
2. Traverse the directory using `os.walk`.
3. Parse each Python file using the `ast` module.
4. Extract import statements and identify imports from the target module.
5. Store and return the results.