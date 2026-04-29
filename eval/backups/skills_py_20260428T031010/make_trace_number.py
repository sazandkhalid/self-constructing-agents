# skill: make_trace_number
# version: 1
# tags: write, function, make_trace_number, routing_number, sequence
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-28T03:03:47.215968+00:00
# decaying: false
# compliance_warn: skill accesses financial/PII data without an audit hook
def make_trace_number(routing_number: str, sequence: int) -> str:
    """
    Generates a 15-digit NACHA trace number.

    The trace number is formed by the first 8 digits of the routing number
    concatenated with a 7-digit zero-padded sequence number.

    Args:
        routing_number: The ABA routing number (string, expected to be at least 8 digits).
        sequence: The transaction sequence number (integer).

    Returns:
        A 15-digit NACHA trace number string.
    """
    if not isinstance(routing_number, str) or len(routing_number) < 8:
        raise ValueError("Routing number must be a string of at least 8 digits.")
    if not isinstance(sequence, int) or sequence < 0:
        raise ValueError("Sequence must be a non-negative integer.")

    # Take the first 8 digits of the routing number
    routing_prefix = routing_number[:8]

    # Pad the sequence number with leading zeros to 7 digits
    padded_sequence = f"{sequence:07d}"

    # Concatenate to form the 15-digit trace number
    trace_number = routing_prefix + padded_sequence

    if len(trace_number) != 15:
        raise RuntimeError(f"Generated trace number has an unexpected length: {len(trace_number)}")

    return trace_number

if __name__ == "__main__":
    # Unit test for make_trace_number
    test_routing_number = "123456789"
    test_sequence_1 = 1
    expected_trace_1 = "123456780000001"
    assert make_trace_number(test_routing_number, test_sequence_1) == expected_trace_1, f"Test Case 1 Failed: Expected {expected_trace_1}, Got {make_trace_number(test_routing_number, test_sequence_1)}"

    test_sequence_2 = 1234567
    expected_trace_2 = "123456781234567"
    assert make_trace_number(test_routing_number, test_sequence_2) == expected_trace_2, f"Test Case 2 Failed: Expected {expected_trace_2}, Got {make_trace_number(test_routing_number, test_sequence_2)}"

    test_routing_number_long = "0123456789012345"
    test_sequence_3 = 99
    expected_trace_3 = "012345670000099"
    assert make_trace_number(test_routing_number_long, test_sequence_3) == expected_trace_3, f"Test Case 3 Failed: Expected {expected_trace_3}, Got {make_trace_number(test_routing_number_long, test_sequence_3)}"

    # Test case for zero sequence
    test_sequence_4 = 0
    expected_trace_4 = "123456780000000"
    assert make_trace_number(test_routing_number, test_sequence_4) == expected_trace_4, f"Test Case 4 Failed: Expected {expected_trace_4}, Got {make_trace_number(test_routing_number, test_sequence_4)}"

    # Test with longer routing number to ensure slicing works correctly
    test_routing_number_very_long = "9876543210123456789"
    test_sequence_5 = 54321
    expected_trace_5 = "987654320054321"
    assert make_trace_number(test_routing_number_very_long, test_sequence_5) == expected_trace_5, f"Test Case 5 Failed: Expected {expected_trace_5}, Got {make_trace_number(test_routing_number_very_long, test_sequence_5)}"

    print("TEST PASSED")
