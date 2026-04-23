---
name: apiroute_construction_skill
tags:
- apiroute
- construction
- pattern
trigger: when constructing APIRoute instances in FastAPI applications
type: pattern
version: 1
success_count: 0
fail_count: 0
---
---
# APIRoute Construction Skill
## Purpose
Abstract the common pattern used to construct APIRoute instances in FastAPI applications.
## When to use
Use this skill when creating custom API routes in FastAPI applications that require a specific construction pattern.
## How to use
1. Import the APIRoute class from fastapi.routing.
2. Create a new APIRoute instance by calling the APIRoute constructor and passing the required parameters, such as the path, endpoint, and methods.
3. Customize the APIRoute instance as needed by setting additional attributes, such as the description, summary, and response model.