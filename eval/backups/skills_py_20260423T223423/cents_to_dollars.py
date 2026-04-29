# skill: cents_to_dollars
# version: 1
# tags: write, python, function, called, cents_to_dollars
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T22:27:40.882495+00:00
# decaying: false
# protocol: general
# rail: general
# audit_required: true
# protocol: general
# rail: general
# audit_required: true
def cents_to_dollars(cents: int) -> float:
    """Converts cents to dollars and rounds to 2 decimal places."""
    return round(cents / 100, 2)

if __name__ == "__main__":
    assert cents_to_dollars(4783250) == 47832.50, f"Expected 47832.50, got {cents_to_dollars(4783250)}"
    assert cents_to_dollars(100) == 1.00, f"Expected 1.00, got {cents_to_dollars(100)}"
    assert cents_to_dollars(50) == 0.50, f"Expected 0.50, got {cents_to_dollars(50)}"
    assert cents_to_dollars(0) == 0.00, f"Expected 0.00, got {cents_to_dollars(0)}"
    print("TEST PASSED")
