---
name: custom_api_route_skill
tags:
- fastapi
- routing
- api_route
trigger: when creating custom API routes in FastAPI with additional attributes
type: pattern
version: 1
success_count: 4
fail_count: 2
---
---
# Custom API Route Skill
## Purpose
Create a new APIRoute subclass that follows the constructor signature and attribute conventions used in `fastapi/routing.py` APIRoute, adding custom attributes as needed.

## When to use
Use this skill when creating custom API routes in FastAPI applications that require additional attributes beyond the standard APIRoute attributes.

## How to use
1. Import the `APIRoute` class from `fastapi.routing`.
2. Create a new class that inherits from `APIRoute`.
3. Define the constructor (`__init__`) method with the required parameters, including the custom attribute(s).
4. Call the parent class constructor using `super().__init__()` and pass the required parameters.
5. Assign the custom attribute(s) to the instance.