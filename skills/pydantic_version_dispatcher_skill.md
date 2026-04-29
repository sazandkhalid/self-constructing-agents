---
name: pydantic_version_dispatcher_skill
tags:
- pydantic
- compatibility
- versioning
- fastapi
trigger: when needing to identify how code dispatches between Pydantic v1 and v2
type: pattern
version: 1
success_count: 1
fail_count: 0
---
---
# Pydantic Version Dispatcher Skill
## Purpose
This skill identifies and abstracts the common patterns used in Python codebases, particularly within frameworks like FastAPI, to conditionally import and utilize components from either Pydantic v1 or Pydantic v2. It focuses on detecting `try-except` blocks that attempt to import from `pydantic.v2` first and fall back to `pydantic.v1`, or similar conditional logic based on version checks.

## When to use
Use this skill when analyzing a Python module (e.g., `fastapi/_compat.py`) that needs to maintain compatibility with both Pydantic v1 and v2. This is especially relevant when the codebase needs to dynamically select which Pydantic version's features to expose or use.

## How to use
1. **Specify the target file:** Provide the path to the Python file that contains the Pydantic version dispatch logic.
2. **Analyze import statements and conditional logic:** Use AST parsing to find import statements related to `pydantic.v1` and `pydantic.v2`.
3. **Identify conditional blocks:** Look for `try-except` statements or `if/else` conditions that are used to determine which Pydantic version's components (like `BaseModel`, `Field`, `create_model`) are imported and aliased.
4. **Extract dispatch pattern:** Abstract the detected logic into a reusable pattern that represents how the codebase switches between Pydantic versions. This pattern should highlight the conditions and the specific components being imported from each version.