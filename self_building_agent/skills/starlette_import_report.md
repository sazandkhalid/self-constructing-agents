---
name: starlette_import_report
tags:
- starlette
- imports
- report
trigger: when generating a report on starlette imports in a FastAPI repository
type: pattern
version: 1
success_count: 3
fail_count: 0
---
---
# Starlette Import Report
## Purpose
Generate a report on the starlette imports in a FastAPI repository, including the number of files that import starlette and the total number of starlette imports.

## When to use
Use this skill when analyzing the starlette imports in a FastAPI repository, especially when trying to identify the usage of starlette in the repository.

## How to use
1. Define the directory path to the FastAPI repository.
2. Use the `find_starlette_imports` function to extract import statements and identify imports from the starlette module.
3. Calculate the number of files that import starlette and the total number of starlette imports.
4. Generate a report based on the calculated statistics.