---
name: dependant_constructor_skill
tags:
- fastapi
- dependencies
- dependant
trigger: when constructing a Dependant object in FastAPI
type: pattern
version: 1
success_count: 1
fail_count: 0
---
---
# Dependant Object Constructor Skill
## Purpose
This skill provides a standardized way to construct a `Dependant` object in FastAPI, ensuring that essential parameters like the dependency callable and caching behavior are correctly set.

## When to use
Use this skill whenever you need to create an instance of FastAPI's `Dependant` class, typically when defining custom dependency injection logic or when programmatically building dependency chains. This is especially useful when the exact path to `fastapi.dependencies.models` might vary or when you want a reliable way to instantiate it without deep knowledge of its internal fields.

## How to use
1. Import the `Dependant` class from `fastapi.dependencies.models`. If the import fails, ensure the file is correctly located or adjust the import path.
2. Call the `dependant_constructor_skill` function with the following arguments:
    - `dependency_callable`: The asynchronous or synchronous function that serves as the dependency. This is a mandatory argument.
    - `use_cache` (optional, defaults to `False`): A boolean indicating whether to cache the dependency's result.
    - `path` (optional, defaults to `None`): The path where the dependency is defined (useful for debugging and introspection).
    - `request_param_name` (optional, defaults to `None`): The name of the parameter in the request that corresponds to this dependency.
    - `cache_bypass_dependency` (optional, defaults to `None`): Another dependency callable that, if called, will bypass the cache.
    - `dependency_overrides_provider` (optional, defaults to `None`): A callable that can provide dependency overrides.

**Example:**

```python
# Assuming Dependant is importable from fastapi.dependencies.models
from fastapi.dependencies.models import Dependant

async def my_async_dependency():
    # ... dependency logic ...
    pass

dependant_obj = dependant_constructor_skill(
    dependency_callable=my_async_dependency,
    use_cache=True,
    path="/some/path"
)

print(f"Dependant object created: {dependant_obj}")
```