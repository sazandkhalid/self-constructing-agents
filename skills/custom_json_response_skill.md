---
name: custom_json_response_skill
tags:
- fastapi
- response
- json
- subclass
- developer_tool
trigger: when creating a custom JSONResponse subclass in FastAPI
type: pattern
version: 1
success_count: 2
fail_count: 0
---
---
# Custom JSONResponse Skill
## Purpose
To generate a boilerplate subclass of `fastapi.responses.JSONResponse` that follows FastAPI's established patterns for custom response types. This allows developers to create specialized JSON responses with pre-defined structures, headers, or behavior.

## When to use
Use this skill when you need to define a custom JSON response class in a FastAPI application that extends `JSONResponse` with specific, repeatable logic or formatting. For example, creating a standardized error response format, a data wrapper, or a response with default headers.

## How to use
1. Identify the specific requirements for your custom JSON response (e.g., additional headers, default status code, custom JSON encoding).
2. Use this skill to generate the base structure of your custom response class.
3. Fill in the specific logic within the generated class, primarily in the `__init__` method or by overriding other methods if necessary.

**Example Usage (Conceptual):**

Imagine you want a `UserResponse` that always includes a specific `X-App-Version` header.

```python
# Using the skill conceptually:
# The skill would generate the following structure, and you'd fill in the details.

from fastapi.responses import JSONResponse
from typing import Any, Dict

class UserResponse(JSONResponse):
    media_type = "application/json"

    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Dict[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ):
        # Add custom header
        custom_headers = {"X-App-Version": "1.0.0"}
        if headers:
            custom_headers.update(headers)

        super().__init__(
            content=content,
            status_code=status_code,
            headers=custom_headers,
            media_type=media_type,
            background=background,
        )

# In your FastAPI app:
# @app.get("/users/{user_id}")
# async def get_user(user_id: str):
#     user_data = {"id": user_id, "name": "John Doe"}
#     return UserResponse(content=user_data)

```

The skill would provide a robust starting point for such custom response classes.