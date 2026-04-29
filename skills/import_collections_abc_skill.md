---
name: import_collections_abc_skill
tags:
- type_hinting
- collections.abc
- pattern
trigger: when identifying repeated import patterns of abstract base classes from collections.abc
  for type hinting purposes.
type: pattern
version: 1
success_count: 1
fail_count: 0
---
---
# Import Collections.abc Skill

## Purpose
To abstract and standardize the import of commonly used abstract base classes from Python's `collections.abc` module. This skill is useful when multiple files within a project repeatedly import the same set of ABCs for type hinting, promoting consistency and reducing redundancy.

## When to use
Use this skill when you observe that several Python files within a project are importing the same group of abstract base classes (e.g., `Callable`, `Generator`, `AsyncGenerator`, `Iterable`, `AsyncIterable`, `AsyncIterator`) from the `collections.abc` module. This is common in projects that heavily utilize type hinting, especially those dealing with asynchronous programming.

## How to use
1.  **Identify the target ABCs:** Determine the specific set of abstract base classes from `collections.abc` that are being imported repeatedly. The most common set includes `Callable`, `Generator`, `AsyncGenerator`, `AsyncIterable`, `AsyncIterator`, `Iterable`.
2.  **Create a central import module:** Create a new Python file (e.g., `fastapi/abc_types.py`) within the project. This file will contain the consolidated import statement.
    ```python
    # Example content for fastapi/abc_types.py
    from collections.abc import (
        AsyncGenerator,
        AsyncIterable,
        AsyncIterator,
        Callable,
        Generator,
        Iterable,
    )

    __all__ = [
        "AsyncGenerator",
        "AsyncIterable",
        "AsyncIterator",
        "Callable",
        "Generator",
        "Iterable",
    ]
    ```
3.  **Update importing files:** Modify the files that were previously importing directly from `collections.abc` to instead import the required types from the newly created skill module. For example, change:
    `from collections.abc import Generator`
    to:
    `from fastapi.abc_types import Generator`
4.  **Verify imports:** Ensure that all type hints and code that relied on the original imports still function correctly after the change.

**Example files demonstrating the pattern:**
*   `./eval/target_repo/fastapi/tests/test_sse.py`
*   `./eval/target_repo/fastapi/tests/test_dependency_wrapped.py`
*   `./eval/target_repo/fastapi/tests/test_dependency_class.py`
*   `./eval/target_repo/fastapi/tests/test_dependency_after_yield_streaming.py`