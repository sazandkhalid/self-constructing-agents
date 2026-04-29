# skill: custom_jsonable_encoder
# version: 1
# tags: look, fastapi, encoders, jsonable_encoder, produce
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T23:16:10.238475+00:00
# decaying: false
from datetime import datetime
from uuid import UUID

def custom_jsonable_encoder(obj: Any) -> Any:
    """
    Encodes Python objects into JSON-serializable formats, similar to FastAPI's jsonable_encoder
    but with a reduced scope for common types like datetime, UUID, and Pydantic-like objects.
    """
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    # This is a placeholder for Pydantic-like objects; a real implementation might check for specific
    # base classes or methods like .model_dump() or .dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    elif isinstance(obj, dict):
        return {k: custom_jsonable_encoder(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [custom_jsonable_encoder(item) for item in obj]
    else:
        # For other types, we rely on the default JSON encoder, which might raise a TypeError
        # if the object is not serializable.
        return obj

if __name__ == "__main__":
    class MockModel:
        def __init__(self, name, value):
            self.name = name
            self.value = value

    test_obj_datetime = datetime(2023, 10, 27, 10, 30, 0)
    test_obj_uuid = UUID("12345678-1234-5678-1234-567812345678")
    test_obj_mock = MockModel("test_name", 123)
    test_obj_dict = {"a": 1, "b": test_obj_datetime, "c": UUID("abcdef01-2345-6789-abcd-ef0123456789")}
    test_obj_list = [test_obj_datetime, test_obj_mock, 5]

    assert custom_jsonable_encoder(test_obj_datetime) == "2023-10-27T10:30:00"
    assert custom_jsonable_encoder(test_obj_uuid) == "12345678-1234-5678-1234-567812345678"
    assert custom_jsonable_encoder(test_obj_mock) == {"name": "test_name", "value": 123}
    assert custom_jsonable_encoder(test_obj_dict) == {"a": 1, "b": "2023-10-27T10:30:00", "c": "abcdef01-2345-6789-abcd-ef0123456789"}
    assert custom_jsonable_encoder(test_obj_list) == ["2023-10-27T10:30:00", {"name": "test_name", "value": 123}, 5]
    assert custom_jsonable_encoder(123) == 123
    assert custom_jsonable_encoder("hello") == "hello"

    print("TEST PASSED")
