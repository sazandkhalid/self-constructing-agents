---
name: module_import_analyzer
tags:
- import analysis
- module imports
trigger: when analyzing imports from a specific module
type: pattern
version: 1
success_count: 14
fail_count: 1
---
---
# Module Import Analyzer
## Purpose
Analyze Python code to identify imports from a specific module.

## When to use
Use this skill when you need to extract imports from a certain module in a Python codebase.

## How to use
1. Define the directory to scan.
2. Traverse the directory using `os.walk`.
3. Parse each Python file using the `ast` module.
4. Extract import statements and identify imports from the target module.
5. Store and return the results.