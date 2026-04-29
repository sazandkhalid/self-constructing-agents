# skill: build_end_to_end_id
# version: 1
# tags: write, function, build_end_to_end_id, sender_ref, date_str
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-28T03:04:58.902235+00:00
# decaying: false
import uuid
from datetime import datetime

# protocol: general
# rail: general
# audit_required: false
def build_end_to_end_id(sender_ref: str, date_str: str) -> str:
    """
    Builds an end-to-end ID string in the format SENDER-YYYYMMDD-UUID4[:8].

    Args:
        sender_ref: The sender's reference string.
        date_str: The date string in YYYYMMDD format.

    Returns:
        A formatted end-to-end ID string.
    """
    if not sender_ref:
        raise ValueError("sender_ref cannot be empty")
    if not date_str:
        raise ValueError("date_str cannot be empty")
    try:
        datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        raise ValueError("date_str must be in YYYYMMDD format")

    uuid_part = str(uuid.uuid4()).replace('-', '')[:8]
    return f"{sender_ref}-{date_str}-{uuid_part}"

if __name__ == "__main__":
    # Test case 1: Basic functionality
    sender = "SENDER123"
    date_val = "20231027"
    expected_format = r"SENDER123-20231027-[0-9a-f]{8}"
    result = build_end_to_end_id(sender, date_val)
    import re
    assert re.fullmatch(expected_format, result), f"Test Case 1 Failed: Expected format {expected_format}, Got {result}"

    # Test case 2: Empty sender_ref
    try:
        build_end_to_end_id("", date_val)
        assert False, "Test Case 2 Failed: Expected ValueError for empty sender_ref"
    except ValueError as e:
        assert str(e) == "sender_ref cannot be empty", f"Test Case 2 Failed: Incorrect error message: {e}"

    # Test case 3: Empty date_str
    try:
        build_end_to_end_id(sender, "")
        assert False, "Test Case 3 Failed: Expected ValueError for empty date_str"
    except ValueError as e:
        assert str(e) == "date_str cannot be empty", f"Test Case 3 Failed: Incorrect error message: {e}"

    # Test case 4: Invalid date format
    try:
        build_end_to_end_id(sender, "27-10-2023")
        assert False, "Test Case 4 Failed: Expected ValueError for invalid date format"
    except ValueError as e:
        assert str(e) == "date_str must be in YYYYMMDD format", f"Test Case 4 Failed: Incorrect error message: {e}"

    # Test case 5: Different sender and date
    sender2 = "ANOTHERREF"
    date_val2 = "20240115"
    expected_format2 = r"ANOTHERREF-20240115-[0-9a-f]{8}"
    result2 = build_end_to_end_id(sender2, date_val2)
    assert re.fullmatch(expected_format2, result2), f"Test Case 5 Failed: Expected format {expected_format2}, Got {result2}"

    print("TEST PASSED")
