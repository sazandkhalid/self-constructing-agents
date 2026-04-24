---
name: fastapi_add_api_route_signature_skill
tags:
- fastapi
- routing
- api_route
- signature
- parameter_ordering
trigger: when needing to understand the parameter order and types for the `add_api_route`
  method in FastAPI's `APIRouter`.
type: pattern
version: 1
success_count: 0
fail_count: 0
---
---
# FastAPI APIRouter add_api_route Signature Skill

## Purpose
This skill documents the parameter ordering and types for the `APIRouter.add_api_route` method in FastAPI. Understanding this signature is essential for correctly defining and adding API routes to an `APIRouter` instance.

## When to use
Use this skill when you need to programmatically add routes to an `APIRouter` instance and are unsure about the correct order and types of arguments for the `add_api_route` method. This is particularly useful when constructing routes dynamically or when referring to the FastAPI source code for implementation details.

## How to use
1. Import `APIRouter` from `fastapi.routing`.
2. Call the `add_api_route` method on an instance of `APIRouter`.
3. Pass arguments in the following order and with the specified types:
    - `path: str`: The path for the route (e.g., "/users/").
    - `endpoint: Callable[..., Any]`: The asynchronous or synchronous function that handles requests to this route.
    - `*,` : This signifies that all subsequent arguments are keyword-only.
    - `response_model: Optional[Type[Any]] = None`: A Pydantic model to use for the response.
    - `status_code: Union[int, Dict[Union[int, str], Union[int, str]]] = 200`: The HTTP status code to return. Can be a single integer or a dictionary mapping HTTP status codes to descriptions.
    - `tags: Optional[List[str]] = None`: A list of tags to associate with this route for OpenAPI documentation.
    - `dependencies: Optional[Sequence[Depends]] = None`: A sequence of dependencies to be executed before the endpoint.
    - `summary: Optional[str] = None`: A short summary of this operation.
    - `description: Optional[str] = None`: A longer description of this operation.
    - `response_description: str = "Successful Response"`: A description of the successful response.
    - `responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None`: A dictionary of possible responses, keyed by HTTP status code.
    - `terms_of_service: Optional[str] = None`: A URL to the Terms of Service for the API.
    - `contact: Optional[Dict[str, Union[str, Any]]] = None`: Contact information for the API.
    - `license_info: Optional[Dict[str, Union[str, Any]]] = None`: License information for the API.
    - `external_docs: Optional[Dict[str, Union[str, Any]]] = None`: External documentation for the API.
    - `redirect_url: Optional[str] = None`: A URL to redirect to if the route is moved.
    - `include_in_schema: bool = True`: Whether to include this route in the OpenAPI schema.
    - `response_model_include: Optional[Union[Set[Union[int, str]], Dict[Union[int, str], Union[int, str]]]] = None`: Fields to include in the response model.
    - `response_model_exclude: Optional[Union[Set[Union[int, str]], Dict[Union[int, str], Union[int, str]]]] = None`: Fields to exclude from the response model.
    - `response_model_by_alias: bool = True`: Whether to use aliases for response model fields.
    - `response_model_exclude_unset: bool = False`: Whether to exclude unset fields from the response model.
    - `response_model_exclude_defaults: bool = False`: Whether to exclude default fields from the response model.
    - `response_model_exclude_none: bool = False`: Whether to exclude None fields from the response model.
    - `deprecated: Optional[bool] = None`: Whether the route is deprecated.
    - `methods: Optional[List[str]] = None`: A list of HTTP methods to allow for this route. If None, it defaults to ["GET"].
    - `operation_id: Optional[str] = None`: An identifier for the operation.
    - `*,`: Another keyword-only argument separator.
    - `exception_handlers: Optional[Dict[Type[Exception], Callable[[Request, Exception], Response]]]] = None`: Exception handlers for this route.
    - `name: Optional[str] = None`: A name for the route. If None, it will be generated from the endpoint function name.
    - `route_class: Type[APIRoute] = APIRoute`: The class to use for the route.
    - `auto_route: bool = False`: Whether to automatically generate the route.

Example of `add_api_route` usage:

```python
from fastapi import FastAPI, APIRouter
from fastapi.routing import APIRoute
from typing import Callable, Any, Optional, Dict, List, Sequence, Type

app = FastAPI()
router = APIRouter()

async def read_root():
    return {"Hello": "World"}

# Example using positional and keyword arguments
router.add_api_route(
    "/",
    endpoint=read_root,
    methods=["GET"],
    response_model=dict[str, str],
    summary="Read the root endpoint",
    tags=["Root"],
    include_in_schema=True,
    response_description="A greeting message"
)

# Example with route_class and other keyword arguments
def custom_route_handler(request: Any, exc: Exception) -> Any:
    return {"error": str(exc)}

class CustomAPIRoute(APIRoute):
    pass

router.add_api_route(
    "/custom",
    endpoint=read_root,
    route_class=CustomAPIRoute,
    exception_handlers={Exception: custom_route_handler},
    name="custom_route_name"
)

app.include_router(router)
```