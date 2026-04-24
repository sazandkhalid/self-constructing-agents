---
name: fastapi_security_scheme_call_pattern
tags:
- fastapi
- security
- pattern
- dependency
trigger: when identifying a common pattern in FastAPI security scheme definitions
  that involves a __call__ method or similar callable behavior for dependency injection.
type: pattern
version: 1
success_count: 3
fail_count: 0
---
---
# FastAPI Security Scheme Call Pattern
## Purpose
To abstract and standardize the common pattern used in FastAPI security schemes where classes are designed to be callable, often used for dependency injection. This pattern typically involves a `__call__` method that encapsulates the security logic.
## When to use
Use this skill when you observe multiple security scheme implementations in FastAPI (e.g., OAuth2, API Key, HTTP Basic/Bearer) that define a `__call__` method to perform security checks and return user information or raise exceptions, enabling their use as FastAPI dependencies.
## How to use
1. **Identify the pattern:** Look for classes within `fastapi/security` or similar modules that define a `__call__(self, ...)` method. This method usually takes request-specific arguments (like `request` from Starlette) and performs authentication/authorization.
2. **Abstract the pattern:** Recognize that the core idea is to make the security scheme instance itself callable to act as a dependency. The `__call__` method's signature and return type/exception raising behavior are key components.
3. **Document the pattern:** Create a skill description (like this one) that details this common structure. This helps in recognizing and reusing this pattern when building custom security schemes or analyzing existing ones. The pattern typically involves:
    - A class inheriting from `SecurityBase` or a similar base class.
    - An `__init__` method to configure the scheme (e.g., with schemes, scopes, or credentials).
    - A `__call__` method that takes request context and performs the security validation.
    - The `__call__` method might return a user object or raise an `HTTPException` on failure.