---
name: import_optimizer
tags:
- import statements
- optimization
trigger: when optimizing import statements in a Python repository
type: pattern
version: 1
success_count: 0
fail_count: 2
---
---
# Import Optimizer
## Purpose
Optimize import statements in a Python repository by removing redundant imports.

## When to use
Use this skill when optimizing import statements in a Python repository.

## How to use
1. Run the `find_repeated_imports` function to identify repeated import statements.
2. Remove redundant import statements from the files where they are found.
3. Use a linter or code formatter to ensure the code remains readable and consistent.