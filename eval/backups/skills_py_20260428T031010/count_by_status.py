# skill: count_by_status
# version: 1
# tags: write, function, count_by_status, results, list
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-28T03:06:44.581149+00:00
# decaying: false
# protocol: general
# rail: general
# audit_required: false
# protocol: general
# rail: general
# audit_required: false
from dataclasses import dataclass
from typing import Any

@dataclass
class MatchResult:
    status: str
    message: Optional[str] = None
    # Add other attributes as needed for testing

def count_by_status(results: list[Any]) -> dict:
    """Counts items in a list by their .status attribute."""
    counts = {}
    for item in results:
        status = getattr(item, 'status', 'unknown') # Safely get status, default to 'unknown'
        counts[status] = counts.get(status, 0) + 1
    return counts

if __name__ == "__main__":
    # Mock MatchResult objects for testing
    @dataclass
    class MockMatchResult:
        status: str

    test_results_1 = [
        MockMatchResult(status="matched"),
        MockMatchResult(status="unmatched"),
        MockMatchResult(status="matched"),
        MockMatchResult(status="rejected"),
        MockMatchResult(status="matched"),
    ]
    expected_counts_1 = {"matched": 3, "unmatched": 1, "rejected": 1}
    actual_counts_1 = count_by_status(test_results_1)
    assert actual_counts_1 == expected_counts_1, f"Test 1 Failed: Expected {expected_counts_1}, Got {actual_counts_1}"

    test_results_2 = []
    expected_counts_2 = {}
    actual_counts_2 = count_by_status(test_results_2)
    assert actual_counts_2 == expected_counts_2, f"Test 2 Failed: Expected {expected_counts_2}, Got {actual_counts_2}"

    test_results_3 = [
        MockMatchResult(status="pending"),
        MockMatchResult(status="pending"),
    ]
    expected_counts_3 = {"pending": 2}
    actual_counts_3 = count_by_status(test_results_3)
    assert actual_counts_3 == expected_counts_3, f"Test 3 Failed: Expected {expected_counts_3}, Got {actual_counts_3}"

    # Test with items missing status attribute
    class NoStatus:
        pass
    test_results_4 = [
        MockMatchResult(status="matched"),
        NoStatus(),
        MockMatchResult(status="unmatched"),
        NoStatus(),
    ]
    expected_counts_4 = {"matched": 1, "unmatched": 1, "unknown": 2}
    actual_counts_4 = count_by_status(test_results_4)
    assert actual_counts_4 == expected_counts_4, f"Test 4 Failed: Expected {expected_counts_4}, Got {actual_counts_4}"


    print("TEST PASSED")
