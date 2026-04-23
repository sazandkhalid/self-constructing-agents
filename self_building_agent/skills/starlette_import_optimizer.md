---
name: starlette_import_optimizer
tags:
- starlette
- fastapi
- import optimizer
trigger: when optimizing starlette imports in the fastapi repository
type: pattern
version: 1
success_count: 0
fail_count: 0
---
---
# Starlette Import Optimizer
## Purpose
Analyze the starlette imports in the fastapi repository and provide recommendations for optimizing import statements.

## When to use
Use this skill when optimizing starlette imports in the fastapi repository, especially when trying to reduce the number of import statements or improve code readability.

## How to use
1. Define the directory path to the fastapi repository.
2. Use the `extract_starlette_imports` function to extract starlette imports from each file.
3. Analyze the import statements and provide recommendations for optimizing them, such as removing unused imports or using wildcard imports.
4. Generate a report based on the analysis and recommendations.