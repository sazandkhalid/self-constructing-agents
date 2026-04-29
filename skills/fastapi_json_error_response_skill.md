---
name: fastapi_json_error_response_skill
tags:
- fastapi
- error-handling
- response-generation
- skill
trigger: when constructing standardized JSON error responses in FastAPI, particularly
  for validation errors or custom HTTP exceptions.
type: pattern
version: 1
success_count: 0
fail_count: 0
---
---
# FastAPI JSON Error Response Skill
## Purpose
To generate a standardized JSON error response payload for FastAPI applications, consistent with how FastAPI's built-in exception handlers format error details. This is particularly useful for `RequestValidationError` and custom `HTTPException` instances.

## When to use
Use this skill when you need to:
- Create custom exception handlers in FastAPI that return a JSON response.
- Ensure consistency in error response formats across your API, especially for validation errors.
- Wrap `HTTPException` or `RequestValidationError` in a predictable JSON structure.

## How to use
1. **Identify the error type and details:** Determine if the error is a `RequestValidationError` (which has specific `errors()` and `errors` attributes) or a custom `HTTPException` (which has a `detail` attribute).
2. **Prepare the content:**
    - For `RequestValidationError`: Extract the validation errors using the `.errors()` method.
    - For `HTTPException`: Use the `detail` attribute of the exception.
    - For other errors: Provide a generic error message.
3. **Construct the JSON response:** Use the `fastapi.responses.JSONResponse` class with the following structure:
    - `content`: A dictionary containing:
        - `"detail"`: The primary error message or list of validation errors.
        - Optionally, `"validation_errors"` if the error is a `RequestValidationError`.
    - `status_code`: The HTTP status code associated with the error.
    - `headers`: Any custom headers required.

**Example Usage (Conceptual):**

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
# Assume fastapi_json_error_response_skill is available and imported as construct_json_error_response

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Use the skill to construct the error response
    return construct_json_error_response(
        detail="Validation error occurred",
        errors=exc.errors(), # Pass the specific errors from the exception
        status_code=422
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Use the skill to construct the error response
    return construct_json_error_response(
        detail=exc.detail,
        status_code=exc.status_code
    )

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id == 5:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id}

# Example of triggering validation error:
# GET /items/abc
```
The skill would encapsulate the logic to create the `JSONResponse` with the appropriate `content` dictionary based on the error type.