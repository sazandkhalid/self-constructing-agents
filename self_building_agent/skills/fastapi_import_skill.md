---
name: fastapi_import_skill
tags:
- fastapi
- import
trigger: When importing the FastAPI class in multiple files across the repository.
type: pattern
version: 1
success_count: 1
fail_count: 0
---
---
# FastAPI Import Skill
## Purpose
Abstract the repeated code pattern of importing the `FastAPI` class from the `fastapi` module into a reusable skill.
## When to use
Use this skill when importing the `FastAPI` class in multiple files across the repository.
## How to use
1. Identify the files that import the `FastAPI` class.
2. Abstract the import statement into a reusable function or class.
3. Apply the abstracted import statement across the repository.

Example source files:
- `fastapi/middleware/asyncexitstack.py`
- `docs_src/stream_data/tutorial001_py310.py`
- `scripts/playwright/cookie_param_models/image01.py`

---END NEW SKILL---

4. Follow-up task:

---NEW TASK---
Search for other repeated code patterns in the repository and abstract them into reusable skills.
---END TASK---

Note: The `fastapi_import_skill` is a conceptual skill and does not require a PY SKILL block. The skill is designed to identify and abstract repeated code patterns, in this case, the import statement of the `FastAPI` class.