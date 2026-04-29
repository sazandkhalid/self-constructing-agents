# skill: re_export_middleware
# version: 1
# tags: read, fastapi, middleware, __init__, produce
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T23:02:30.934646+00:00
# decaying: false
def re_export_middleware(starlette_module_name: str, middleware_name: str) -> str:
    """
    Generates a Python string to re-export a Starlette middleware with a FastAPI-like naming convention.

    Args:
        starlette_module_name: The name of the Starlette module (e.g., 'starlette.middleware').
        middleware_name: The name of the middleware class in Starlette (e.g., 'Middleware').

    Returns:
        A Python string representing the re-export statement.
    """
    return f"from {starlette_module_name} import {middleware_name} as {middleware_name}"

if __name__ == "__main__":
    # Test case based on fastapi/middleware/__init__.py
    test_module = "starlette.middleware"
    test_middleware = "Middleware"
    expected_output = "from starlette.middleware import Middleware as Middleware"
    result = re_export_middleware(test_module, test_middleware)
    assert result == expected_output, f"Test Case 1 Failed: Expected '{expected_output}', got '{result}'"

    # Test case based on fastapi/middleware/trustedhost.py
    test_module_2 = "starlette.middleware.trustedhost"
    test_middleware_2 = "TrustedHostMiddleware"
    expected_output_2 = "from starlette.middleware.trustedhost import TrustedHostMiddleware as TrustedHostMiddleware"
    result_2 = re_export_middleware(test_module_2, test_middleware_2)
    assert result_2 == expected_output_2, f"Test Case 2 Failed: Expected '{expected_output_2}', got '{result_2}'"

    print("TEST PASSED")
