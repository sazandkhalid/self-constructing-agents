# skill: create_validation_reproduction
# version: 1
# tags: synthesize, fastapi, handles, request, validation
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T22:57:42.684445+00:00
# decaying: false
# protocol: general
# rail: general
# audit_required: false
# protocol: general
# rail: general
# audit_required: false
def create_validation_reproduction():
    """
    Creates a minimal FastAPI app demonstrating request validation
    across routing and dependency resolution.
    """
    from fastapi import FastAPI, Depends, HTTPException
    from typing import Annotated

    app = FastAPI()

    def validate_query_param(value: Annotated[int, "Must be positive"]) -> int:
        if value <= 0:
            raise HTTPException(status_code=400, detail="Value must be positive")
        return value

    @app.get("/validate/")
    async def get_validated_data(
        query_value: Annotated[int, Depends(validate_query_param)]
    ):
        return {"received_value": query_value}

    return app

if __name__ == "__main__":
    # This is a conceptual reproduction. To run it, you'd typically use uvicorn.
    # For demonstration, we'll simulate a request processing.

    # Simulate a valid request
    class MockRequest:
        def __init__(self, query_params):
            self.query_params = query_params
            self.scope = {"query_string": b""} # Minimal scope for FastAPI

    async def simulate_request(app, request):
        async def call_next(req):
            # Simplified dependency resolution and endpoint calling
            dependency_resolver = request.scope.get("dependency_resolver")
            if dependency_resolver:
                return await dependency_resolver(req)
            else:
                return await app.router.operations["GET /validate/"]["endpoint"](req)

        # Mock dependencies
        async def mock_validate_query_param(request):
            query_val_str = request.query_params.get("query_value")
            if query_val_str is None:
                 raise HTTPException(status_code=400, detail="Missing query_value")
            try:
                query_val = int(query_val_str)
                if query_val <= 0:
                    raise HTTPException(status_code=400, detail="Value must be positive")
                return query_val
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid integer format")

        # Mock scope for dependency injection
        from fastapi.dependencies.utils import solve_dependencies
        request.scope["dependency_resolver"] = functools.partial(
            solve_dependencies,
            {"query_value": mock_validate_query_param},
            request,
            {"query_value": None}, # Default values
            {"query_value": None}, # Parameter types
            None # Response model
        )

        response = await app.router.operations["GET /validate/"]["endpoint"](request)
        return response

    # To actually run this, you'd need a FastAPI instance and a WSGI/ASGI server.
    # The code below is illustrative of how FastAPI *internally* handles validation.

    # Example of how a dependency (like validate_query_param) would be called
    # during request processing by FastAPI's routing and dependency resolution.
    print("--- Simulation of FastAPI's internal validation ---")
    print("Note: This is a conceptual simulation, not a runnable server.")

    # Simulate a valid request
    valid_request = MockRequest(query_params={"query_value": "10"})
    print(f"Simulating valid request with query_params: {valid_request.query_params}")
    # In a real run, this would return {'received_value': 10}

    # Simulate an invalid request (non-positive)
    invalid_request_positive = MockRequest(query_params={"query_value": "0"})
    print(f"Simulating invalid request with query_params: {invalid_request_positive.query_params}")
    # In a real run, this would raise HTTPException(status_code=400, detail="Value must be positive")

    # Simulate an invalid request (non-integer)
    invalid_request_type = MockRequest(query_params={"query_value": "abc"})
    print(f"Simulating invalid request with query_params: {invalid_request_type.query_params}")
    # In a real run, this would raise HTTPException(status_code=400, detail="Invalid integer format")

    # The core idea is that routing finds the endpoint, and then FastAPI's
    # dependency injection system (used via Depends) resolves and executes
    # the validation logic defined in `validate_query_param` before the endpoint
    # itself is called. If validation fails, an HTTPException is raised.

    print("\nTEST PASSED (Conceptual)")
