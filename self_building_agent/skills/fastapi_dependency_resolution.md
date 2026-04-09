---
name: fastapi_dependency_resolution
tags:
- fastapi
- dependencies
- resolution
trigger: when resolving dependency callables in FastAPI applications
type: pattern
version: 1
success_count: 0
fail_count: 1
---
---
# FastAPI Dependency Resolution
## Purpose
Resolve dependency callables in FastAPI applications by inspecting the callable and its annotations.

## When to use
Use this skill when resolving dependency callables in FastAPI applications, particularly when working with the `fastapi/dependencies/utils.py` file.

## How to use
1. Import the `inspect` module to inspect the callable and its annotations.
2. Check if the callable is a function using `inspect.isfunction`.
3. If the callable is a function, return the resolved callable.
4. Otherwise, raise a `ValueError` to indicate that only functions are supported.