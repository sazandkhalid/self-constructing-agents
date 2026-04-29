---
name: depends_cached_skill
tags:
- fastapi
- dependency-injection
- caching
trigger: when needing to create a FastAPI dependency that caches its results based
  on input arguments.
type: pattern
version: 1
success_count: 2
fail_count: 0
---
---
# DependsCached Skill

## Purpose
To provide a reusable FastAPI dependency helper that caches its results based on the arguments it's called with, improving performance for expensive dependency computations.

## When to use
Use this skill when you have a FastAPI dependency function that is computationally expensive or makes external calls, and its output is consistent for the same set of input arguments. This can significantly speed up request processing by avoiding redundant computations.

## How to use
1.  **Import `DependsCached`**:
    ```python
    from fastapi import FastAPI
    from your_skills_module import DependsCached # Assuming the skill is saved and imported
    ```
2.  **Define your dependency function**: This function can be `async` or regular.
    ```python
    async def expensive_data_fetch(user_id: int, include_details