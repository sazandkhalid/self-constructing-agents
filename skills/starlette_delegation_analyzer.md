---
name: starlette_delegation_analyzer
tags:
- starlette
- fastapi
- import-analysis
- pattern-abstraction
trigger: when identifying recurring patterns of importing specific components from
  Starlette into FastAPI modules
type: pattern
version: 1
success_count: 2
fail_count: 5
---
---
# Starlette Delegation Analyzer
## Purpose
To identify and report on the pattern of importing specific components from the Starlette library into FastAPI modules. This skill helps in understanding the architectural relationship between FastAPI and Starlette, identifying key dependencies, and potentially discovering areas for optimization or refactoring related to these imports.
## When to use
Use this skill when analyzing the FastAPI codebase and observing a recurring pattern where specific classes, functions, or modules from Starlette are imported into various FastAPI internal files. This is particularly useful when:
*   Trying to understand how FastAPI extends or utilizes Starlette's functionality.
*   Investigating dependencies on specific Starlette features.
*   Looking for opportunities to streamline or optimize imports within the FastAPI project.
*   Documenting the core architectural components that FastAPI relies on from Starlette.
## How to use
1.  **Specify the target directory:** Provide the path to the directory containing the Python source code to be analyzed (e.g., the root `fastapi/` directory).
2.  **Execute the analysis:** Run the `analyze_starlette_imports_in_directory` function (or a similar implementation) with the specified directory path. This function should recursively scan all `.py` files, parse their Abstract Syntax Trees (AST), and extract import statements originating from `starlette`.
3.  **Review the results:** The output will be a dictionary where keys are the file paths containing `starlette` imports, and values are lists of the import statements found in each file.
4.  **Interpret the findings:** Analyze the collected import information to identify common Starlette components being used across different FastAPI modules. This can inform decisions about code structure, dependency management, and potential performance improvements.