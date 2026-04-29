---
name: reexport_starlette_middleware_skill
tags:
- middleware
- starlette
- fastapi
- re-export
trigger: when re-exporting Starlette middleware with FastAPI naming conventions
type: pattern
version: 1
success_count: 0
fail_count: 0
---
---
# Re-export Starlette Middleware Skill
## Purpose
This skill formalizes the pattern of re-exporting Starlette middleware components with FastAPI's naming conventions, ensuring consistency across the FastAPI project.

## When to use
Use this skill when you need to import Starlette middleware into a FastAPI project and re-export it under a FastAPI-specific name or convention. This is particularly useful for maintaining a consistent API and simplifying imports for users of the FastAPI library.

## How to use
1. Identify the Starlette middleware class you wish to re-export (e.g., `TrustedHostMiddleware` from `starlette.middleware.trustedhost`).
2. In the `fastapi/middleware/__init__.py` (or a similar top-level `__init__.py` file for middleware), add an import statement for the Starlette middleware.
3. Re-export the imported middleware using the desired FastAPI naming convention. For example, if Starlette's `TrustedHostMiddleware` is imported, you might re-export it as `TrustedHostMiddleware` directly if that's the convention, or under a slightly modified name if needed for clarity or to avoid naming conflicts.

   ```python
   # Example: Re-exporting TrustedHostMiddleware
   from starlette.middleware.trustedhost import TrustedHostMiddleware as TrustedHostMiddleware

   # ... other middleware re-exports ...

   __all__ = [
       "Middleware",  # Assuming Middleware itself is also re-exported
       "TrustedHostMiddleware",
       # ... other re-exported middleware names
   ]
   ```
4. Ensure the re-exported name is included in the `__all__` list at the top of the file to control public exports.