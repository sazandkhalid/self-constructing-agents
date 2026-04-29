# skill: custom_jsonable_encoder
# version: 1
# tags: look, fastapi, encoders, jsonable_encoder, produce
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T23:01:38.192835+00:00
# decaying: false
import datetime
from collections.abc import Callable
from decimal import Decimal
from enum import Enum
from typing import Any

def custom_jsonable_encoder(obj: Any) -> Any:
    """
    A simplified, reusable JSON encoder that dispatches to specific handlers
    for common types, similar to FastAPI's jsonable_encoder.
    """
    if obj is None:
        return None
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, datetime.time):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, Enum):
        return obj.value
    elif hasattr(obj, "model_dump"):  # Pydantic v2
        return obj.model_dump()
    elif hasattr(obj, "dict"):  # Pydantic v1
        return obj.dict()
    elif dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    else:
        # For types not explicitly handled, rely on default JSON encoding
        # or raise an error if un-encodable.
        # In a real-world scenario, you might want to add more type handlers
        # or a fallback mechanism.
        try:
            return json.dumps(obj) # Attempt to use json.dumps for built-in types
        except TypeError:
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

# Example Usage & Test (requires pydantic to be installed for Pydantic model tests)
if __name__ == "__main__":
    from pydantic import BaseModel
    import json
    import dataclasses

    class MyPydanticModel(BaseModel):
        name: str
        value: int

    @dataclasses.dataclass
    class MyDataClass:
        field1: str
        field2: float

    class MyEnum(Enum):
        OPTION1 = "opt1"
        OPTION2 = "opt2"

    # Test cases
    test_obj_datetime = datetime.datetime(2023, 10, 27, 10, 30, 0)
    assert custom_jsonable_encoder(test_obj_datetime) == "2023-10-27T10:30:00"

    test_obj_decimal = Decimal("123.45")
    assert custom_jsonable_encoder(test_obj_decimal) == "123.45"

    test_obj_enum = MyEnum.OPTION1
    assert custom_jsonable_encoder(test_obj_enum) == "opt1"

    test_obj_pydantic = MyPydanticModel(name="Test", value=100)
    assert custom_jsonable_encoder(test_obj_pydantic) == {"name": "Test", "value": 100}

    test_obj_dataclass = MyDataClass(field1="hello", field2=1.23)
    assert custom_jsonable_encoder(test_obj_dataclass) == {"field1": "hello", "field2": 1.23}

    test_obj_none = None
    assert custom_jsonable_encoder(test_obj_none) is None

    test_obj_int = 123
    assert custom_jsonable_encoder(test_obj_int) == "123" # json.dumps(123) is "123"

    test_obj_list = [1, "a", None]
    assert custom_jsonable_encoder(test_obj_list) == "[1, \"a\", null]" # json.dumps([1, "a", None])

    # Test for un-encodable type (will raise TypeError)
    class Unencodable:
        pass
    try:
        custom_jsonable_encoder(Unencodable())
    except TypeError as e:
        assert "Object of type Unencodable is not JSON serializable" in str(e)
        print("Unencodable type test passed.")

    print("TEST PASSED")
