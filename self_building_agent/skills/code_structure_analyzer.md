---
name: code_structure_analyzer
tags:
- code_analysis
- repository_organization
trigger: when analyzing the code structure of a repository
type: pattern
version: 1
success_count: 24
fail_count: 7
---
---
# Code Structure Analyzer
## Purpose
Analyze the code structure and organization of a repository to identify patterns, trends, and areas for improvement.
## When to use
Use this skill when analyzing the code structure of a repository, such as the `fastapi` repository.
## How to use
1. Define the repository to analyze.
2. Use the `ast` module to parse the abstract syntax tree of each Python file.
3. Extract information about the code structure, such as class definitions, method names, and attribute names.
4. Analyze the extracted information to identify patterns, trends, and areas for improvement.