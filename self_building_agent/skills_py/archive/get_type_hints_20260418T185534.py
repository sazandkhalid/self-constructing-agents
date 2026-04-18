# skill: get_type_hints
# version: 1
# tags: find, code, pattern, repeated, across
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-09T01:40:43.841069+00:00
# decaying: false
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Callable,
    Generator,
    Iterable,
)

def get_type_hints() -> dict:
    """
    Returns a dictionary of type hints from collections.abc.
    """
    type_hints = {
        "AsyncGenerator": AsyncGenerator,
        "AsyncIterable": AsyncIterable,
        "AsyncIterator": AsyncIterator,
        "Callable": Callable,
        "Generator": Generator,
        "Iterable": Iterable,
    }
    return type_hints

if __name__ == "__main__":
    type_hints = get_type_hints()
    for key, value in type_hints.items():
        assert isinstance(key, str)
        assert callable(value)
    print("TEST PASSED")
