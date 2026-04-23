---
name: import_analyzer
tags:
- import
- analyze
- repository
trigger: When analyzing imports in a repository to identify frequently used modules
  or detect potential import conflicts.
type: pattern
version: 1
success_count: 4
fail_count: 0
---
---
# Import Analyzer Skill
## Purpose
Analyze imports in a given repository to identify frequently used modules, detect potential import conflicts, and generate reports on import usage.

## When to use
Use this skill when working with large repositories with complex import structures, or when trying to identify the most frequently used modules in a project.

## How to use
1. Identify the repository or directory to analyze.
2. Use the `analyze_imports` function to analyze imports in each file.
3. Generate a report on the most frequently imported modules.
4. Use the report to identify potential import conflicts or optimize import statements.