---
name: depends_cached
tags:
- fastapi
- caching
- dependency
trigger: when using FastAPI and needing to cache dependencies
type: pattern
version: 1
success_count: 1
fail_count: 1
---
---
# Depends Cached
## Purpose
Enable caching of dependencies in FastAPI using the `DependsCached` helper.

## When to use
Use this skill when you need to cache the results of dependencies in FastAPI to improve performance.

## How to use
1. Create a `DependsCached` instance with the dependency function and optional cache flag.
2. Use the `DependsCached` instance as a dependency in your FastAPI routes.