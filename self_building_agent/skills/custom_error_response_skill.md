---
name: custom_error_response_skill
tags:
- fastapi
- response
- error_handling
- json
trigger: when needing to create a standardized JSON error response in FastAPI
type: pattern
version: 1
success_count: 0
fail_count: 0
---
---
# Custom Error Response Skill
## Purpose
To generate a boilerplate subclass of `fastapi.responses.JSONResponse` specifically designed for standardized error reporting. This skill aids in creating consistent error payloads across an API, improving client-side error handling and API maintainability.

## When to use
Use this skill when you need to define a custom JSON response class in a FastAPI application to uniformly format error messages. This is particularly useful for:
- Centralizing error reporting for exceptions.
- Providing consistent error codes and details to API consumers.
- Integrating with custom exception handlers in FastAPI.

## How to use
1. **Define Error Structure:** Determine the fields your error response should contain (e.g., `code`, `message`, `details`, `timestamp`).
2. **Generate Class:** Use this skill to create a `CustomErrorResponse` class that inherits from `fastapi.responses.JSONResponse`.
3. **Implement `__init__`:** Customize the `__init__` method to accept error-specific parameters and format the `content` accordingly. You may also want to set a default error status code (e.g., 400, 422, 500).
4. **Integrate with Exception Handlers:** Use this custom response class within your FastAPI application's exception handlers to return structured errors.

**Example Usage:**

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict, Optional

# --- Custom Error Response Skill Usage ---

class CustomErrorResponse(JSONResponse):
    """
    A custom JSONResponse for standardized error reporting.
    """
    media_type = "application/json"

    def __init__(
        self,
        message: str,
        code: int | None = None,
        details: Any = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: Dict[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ):
        error_content = {
            "error": {
                "code": code,
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "details": details,
            }
        }
        
        # Ensure status_code is set correctly if not provided explicitly
        if status_code is None:
            status_code = status.HTTP_400_BAD_REQUEST

        super().__init__(
            content=error_content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

# --- FastAPI Application Example ---

app = FastAPI()

class Item(BaseModel):
    id: str
    value: str

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    return {"message": "Item created successfully", "item": item.dict()}

# Example of using CustomErrorResponse in an exception handler
@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return CustomErrorResponse(
        message=str(exc),
        code=1001, # Example custom error code
        details={"path": request.url.path},
        status_code=status.HTTP_400_BAD_REQUEST
    )

@app.get("/trigger-error")
async def trigger_error():
    raise ValueError("This is a test value error")

# To test:
# Send a POST request to /items/ with valid JSON.
# Send a GET request to /trigger-error to see the custom error response.
```