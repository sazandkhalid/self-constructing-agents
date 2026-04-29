# skill: dollars_to_cents
# version: 1
# tags: write, function, dollars_to_cents, amount, float
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-28T03:04:27.789555+00:00
# decaying: false
# protocol: general
# rail: general
# audit_required: true
# protocol: general
# rail: general
# audit_required: true
def dollars_to_cents(amount: float) -> int:
    """
    Converts an amount in dollars to cents using round-half-up semantics.

    Args:
        amount: The amount in dollars (float).

    Returns:
        The equivalent amount in cents (integer).
    """
    # The `round()` function in Python 3 rounds to the nearest even number for .5 cases.
    # To achieve round-half-up, we add a small epsilon before rounding,
    # or use Decimal for more precise control. Using Decimal is preferred for financial calculations.
    from decimal import Decimal, ROUND_HALF_UP
    return int(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) * 100)

if __name__ == "__main__":
    # Test case for round-half-up
    amount_dollars = 1.005
    expected_cents = 101
    actual_cents = dollars_to_cents(amount_dollars)
    assert actual_cents == expected_cents, f"Test failed for {amount_dollars} dollars: expected {expected_cents} cents, got {actual_cents} cents."

    # Additional test cases
    assert dollars_to_cents(0.99) == 99, "Test failed for 0.99 dollars"
    assert dollars_to_cents(1.00) == 100, "Test failed for 1.00 dollars"
    assert dollars_to_cents(1.01) == 101, "Test failed for 1.01 dollars"
    assert dollars_to_cents(1.999) == 200, "Test failed for 1.999 dollars"
    assert dollars_to_cents(0.001) == 0, "Test failed for 0.001 dollars"
    assert dollars_to_cents(0.005) == 1, "Test failed for 0.005 dollars"
    assert dollars_to_cents(0.004) == 0, "Test failed for 0.004 dollars"
    assert dollars_to_cents(-1.005) == -101, "Test failed for -1.005 dollars"
    print("TEST PASSED")
