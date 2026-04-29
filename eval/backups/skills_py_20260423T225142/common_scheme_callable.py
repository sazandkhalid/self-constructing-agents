# skill: common_scheme_callable
# version: 1
# tags: inspect, fastapi, security, extract, common
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T22:37:18.089850+00:00
# decaying: false
# common_scheme_callable
import inspect
from collections.abc import Callable
from typing import Any

# Assume this is the actual implementation found in fastapi/security/utils.py
# For demonstration purposes, we'll define a simplified version here.
# In a real scenario, we would read the file content and parse it.

def common_scheme_callable(
    scheme: Callable[..., Any]
) -> Callable[..., Any]:
    """
    Extracts the common __call__ pattern from a security scheme callable in FastAPI.

    This function is a simplified representation of how FastAPI might handle
    security schemes, focusing on ensuring the callable has a __call__ method.
    In the context of fastapi/security, schemes often are classes with a __call__
    method. This skill aims to extract that callable part if it exists, or
    ensure the provided callable itself is suitable.
    """
    if inspect.isfunction(scheme):
        # If it's already a function, it's good to go for this simplified skill.
        return scheme
    elif hasattr(scheme, "__call__") and inspect.ismethod(getattr(scheme, "__call__")):
        # If it has a __call__ method, return that. This is common for classes.
        return getattr(scheme, "__call__")
    else:
        raise TypeError("Scheme must be a callable function or an object with a __call__ method")

def test_common_scheme_callable():
    # Test with a simple function
    def simple_func_scheme():
        return "simple_func"

    resolved_func = common_scheme_callable(simple_func_scheme)
    assert resolved_func == simple_func_scheme, f"Expected {simple_func_scheme}, got {resolved_func}"

    # Test with a class that has a __call__ method
    class CallableClassScheme:
        def __call__(self):
            return "callable_class"

    scheme_instance = CallableClassScheme()
    resolved_call = common_scheme_callable(scheme_instance)
    assert resolved_call == scheme_instance.__call__, f"Expected {scheme_instance.__call__}, got {resolved_call}"

    # Test with a class that is callable but not via __call__ (this would fail, as expected for this simplified skill)
    # In a real FastAPI scenario, this would be handled differently, but for the __call__ pattern, this is correct.
    class NonCallableClass:
        pass

    try:
        common_scheme_callable(NonCallableClass())
        assert False, "TypeError was not raised for non-callable class"
    except TypeError:
        # Expected exception
        pass

    # Test with an invalid type
    try:
        common_scheme_callable(123)
        assert False, "TypeError was not raised for invalid type"
    except TypeError:
        # Expected exception
        pass

test_common_scheme_callable()
print("TEST PASSED")
