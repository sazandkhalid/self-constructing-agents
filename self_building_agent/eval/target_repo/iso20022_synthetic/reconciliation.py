"""
Cross-rail transaction reconciliation utilities.
Matches payments across ISO 20022 MX, ACH, and internal ledger records.
"""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

@dataclass
class LedgerEntry:
    entry_id: str
    amount: Decimal
    currency: str
    counterparty: Optional[str]
    reference: Optional[str]
    rail: str   # "iso20022", "ach", "fedwire", "internal"

@dataclass
class MatchResult:
    status: str     # "matched", "unmatched", "partial", "duplicate"
    entry_a: LedgerEntry
    entry_b: Optional[LedgerEntry]
    confidence: float   # 0.0 to 1.0
    reason: str

def match_by_reference(entries_a: list, entries_b: list) -> list:
    """
    Attempt to reconcile two sets of ledger entries by reference field.
    Returns a MatchResult for every entry in entries_a.
    """
    index_b = {e.reference: e for e in entries_b if e.reference}
    results = []
    for a in entries_a:
        b = index_b.get(a.reference)
        if b is None:
            results.append(MatchResult("unmatched", a, None, 0.0, "no reference match"))
        elif a.amount == b.amount and a.currency == b.currency:
            results.append(MatchResult("matched", a, b, 1.0, "exact reference + amount"))
        elif a.currency == b.currency:
            diff_pct = float(abs(a.amount - b.amount) / max(a.amount, b.amount))
            results.append(MatchResult(
                "partial", a, b,
                round(1.0 - diff_pct, 4),
                f"reference match, amount differs by {diff_pct:.1%}"
            ))
        else:
            results.append(MatchResult("unmatched", a, b, 0.3, "reference match but currency mismatch"))
    return results

def surface_exceptions(results: list) -> list:
    """Return only unmatched and partial results, sorted by confidence ascending."""
    return sorted(
        [r for r in results if r.status != "matched"],
        key=lambda r: r.confidence
    )


if __name__ == "__main__":
    a1 = LedgerEntry("A1", Decimal("100.00"), "USD", "Alice", "REF001", "iso20022")
    a2 = LedgerEntry("A2", Decimal("200.00"), "USD", "Bob",   "REF002", "ach")
    a3 = LedgerEntry("A3", Decimal("50.00"),  "USD", "Carol", "REF003", "iso20022")

    b1 = LedgerEntry("B1", Decimal("100.00"), "USD", "Alice", "REF001", "ach")
    b2 = LedgerEntry("B2", Decimal("199.00"), "USD", "Bob",   "REF002", "ach")

    results = match_by_reference([a1, a2, a3], [b1, b2])
    assert results[0].status == "matched"
    assert results[1].status == "partial"
    assert results[2].status == "unmatched"

    exceptions = surface_exceptions(results)
    assert all(r.status != "matched" for r in exceptions)
    print("TEST PASSED")
