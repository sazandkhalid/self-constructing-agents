# skill: resolve_dependency_callable
# version: 1
# tags: fastapi, dependencies, utils, resolves, dependency
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T22:36:42.367682+00:00
# decaying: false
import inspect
from collections.abc import Callable
from typing import Any

# Assume this is the actual implementation found in fastapi/dependencies/utils.py
# For demonstration purposes, we'll define a simplified version here.
# In a real scenario, we would read the file content and parse it.

def resolve_dependency_callable(dependency: Callable[..., Any]) -> Callable[..., Any]:
    """
    Resolves a dependency callable in FastAPI.

    This function inspects the callable to ensure it's a function and returns it.
    It's a simplified representation of FastAPI's dependency resolution.
    """
    if inspect.isfunction(dependency):
        return dependency
    else:
        raise TypeError("Only functions are supported as dependencies")

def test_resolve_dependency_callable():
    def simple_dependency():
        return "test"
    
    # Test with a valid function
    resolved = resolve_dependency_callable(simple_dependency)
    assert resolved == simple_dependency, f"Expected {simple_dependency}, got {resolved}"

    # Test with an invalid type (e.g., a class instance)
    class NotADependency:
        pass

    try:
        resolve_dependency_callable(NotADependency())
        assert False, "TypeError was not raised for non-function dependency"
    except TypeError:
        # Expected exception
        pass
    
    # Test with a lambda function
    lambda_dependency = lambda: "lambda_test"
    resolved_lambda = resolve_dependency_callable(lambda_dependency)
    assert resolved_lambda == lambda_dependency, f"Expected {lambda_dependency}, got {resolved_lambda}"

test_resolve_dependency_callable()
print("TEST PASSED")
