---
name: resolve_fastapi_route_conflicts
tags:
- fastapi
- routing
- conflicts
trigger: When multiple routes with the same name or path are defined in a FastAPI
  application.
type: pattern
version: 1
success_count: 0
fail_count: 2
---
---
# Resolve FastAPI Route Conflicts
## Purpose
Resolve conflicts between multiple routes with the same name or path in a FastAPI application.

## When to use
Use this skill when multiple routes with the same name or path are defined in a FastAPI application, and the correct route needs to be resolved based on additional context or configuration.

## How to use
1. Define the context or configuration that will be used to resolve the route conflict.
2. Traverse the routes and extract information about the conflicting routes.
3. Use the context or configuration to determine the correct route.
4. Return the correct route and its corresponding endpoint.