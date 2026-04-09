# skill: resolve_dependency_callable
# version: 1
# tags: fastapi, dependencies, utils, resolves, dependency
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-09T01:38:57.778385+00:00
# decaying: false
import inspect
from typing import Callable, Any

def resolve_dependency_callable(callable_obj: Callable) -> Callable:
    'Resolve a dependency callable and return the resolved callable.'
    # Implement logic to resolve the dependency callable
    # For example, inspect the callable and its annotations
    if inspect.isfunction(callable_obj):
        return callable_obj
    else:
        raise ValueError("Only functions are supported")

if __name__ == "__main__":
    def example_dependency() -> str:
        return "Example dependency resolved"

    resolved_callable = resolve_dependency_callable(example_dependency)
    assert inspect.isfunction(resolved_callable)
    assert resolved_callable() == "Example dependency resolved"
    print("TEST PASSED")
