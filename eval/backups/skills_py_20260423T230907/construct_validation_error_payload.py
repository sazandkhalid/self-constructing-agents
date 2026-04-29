# skill: construct_validation_error_payload
# version: 1
# tags: read, fastapi, exception_handlers, write, skill
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T23:00:43.630130+00:00
# decaying: false
def construct_validation_error_payload(error_details: list, error_type: str = "validation_error") -> dict:
    """
    Constructs a JSON response payload for validation errors in a FastAPI-like structure.

    Args:
        error_details: A list of dictionaries, where each dictionary contains details
                       about a validation error (e.g., 'loc', 'msg', 'type').
        error_type: The type of error, defaults to 'validation_error'.

    Returns:
        A dictionary representing the error payload.
    """
    # This structure is inspired by FastAPI's RequestValidationError response.
    # The outer structure contains a top-level error type and a list of errors.
    # Each error in the list has location, message, and type information.
    return {
        "type": error_type,
        "errors": error_details
    }

if __name__ == "__main__":
    # Example usage based on typical Pydantic/FastAPI validation error structure
    sample_error_details_1 = [
        {
            "loc": ["body", "email"],
            "msg": "value is not a valid email address",
            "type": "value_error.email"
        },
        {
            "loc": ["query", "page"],
            "msg": "ensure this value is a positive integer",
            "type": "value_error.number.min_value",
            "ctx": {"limit_value": 1}
        }
    ]
    expected_payload_1 = {
        "type": "validation_error",
        "errors": sample_error_details_1
    }
    actual_payload_1 = construct_validation_error_payload(sample_error_details_1)
    assert actual_payload_1 == expected_payload_1, f"Test Case 1 Failed: Expected {expected_payload_1}, Got {actual_payload_1}"

    sample_error_details_2 = [
        {
            "loc": ["path", "item_id"],
            "msg": "value is not a valid integer",
            "type": "type_error.integer"
        }
    ]
    expected_payload_2 = {
        "type": "validation_error",
        "errors": sample_error_details_2
    }
    actual_payload_2 = construct_validation_error_payload(sample_error_details_2)
    assert actual_payload_2 == expected_payload_2, f"Test Case 2 Failed: Expected {expected_payload_2}, Got {actual_payload_2}"

    # Test with a different error type
    sample_error_details_3 = [
        {"loc": ["header", "x-auth"], "msg": "API key missing", "type": "auth.missing_key"}
    ]
    expected_payload_3 = {
        "type": "authentication_error",
        "errors": sample_error_details_3
    }
    actual_payload_3 = construct_validation_error_payload(sample_error_details_3, error_type="authentication_error")
    assert actual_payload_3 == expected_payload_3, f"Test Case 3 Failed: Expected {expected_payload_3}, Got {actual_payload_3}"

    print("TEST PASSED")
