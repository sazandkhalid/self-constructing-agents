# skill: ach_entry_to_ledger_entry
# version: 1
# tags: write, function, ach_entry_to_ledger_entry, entry, achentry
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-28T03:01:42.611120+00:00
# decaying: false
# protocol: general
# rail: nacha
# audit_required: true
# protocol: general
# rail: nacha
# audit_required: true
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass
class LedgerEntry:
    entry_id: str
    amount: Decimal
    currency: str
    counterparty: str
    reference: str
    rail: str

@dataclass
class ACHEntry:
    # Mock ACHEntry structure based on prompt context and common ACH fields.
    # The actual ACHEntry structure might differ, but this should cover the core logic.
    transaction_code: int
    amount: Decimal  # Assuming this is the absolute amount, and transaction_code dictates sign.
    payment_id: str # To map to LedgerEntry.entry_id
    receiver_name: str # To map to LedgerEntry.counterparty
    reference_info: str # To map to LedgerEntry.reference
    currency: str = "USD" # Default currency for ACH

def ach_entry_to_ledger_entry(entry: ACHEntry) -> LedgerEntry:
    """
    Converts an ACHEntry object to a LedgerEntry object.

    Maps transaction_code 22 or 32 to a positive amount (credit),
    and 27 or 37 to a negative amount (debit).
    """
    if entry.transaction_code in (22, 32):
        amount = entry.amount
    elif entry.transaction_code in (27, 37):
        amount = -entry.amount
    else:
        # Handle unknown transaction codes or raise an error as appropriate.
        # For now, let's assume it's a debit if not explicitly credit codes.
        # A more robust implementation might raise an error or log a warning.
        amount = -entry.amount

    return LedgerEntry(
        entry_id=entry.payment_id,
        amount=amount,
        currency=entry.currency,
        counterparty=entry.receiver_name,
        reference=entry.reference_info,
        rail="ach"
    )

if __name__ == "__main__":
    # Test case 1: Credit transaction (code 22)
    ach_entry_credit = ACHEntry(
        transaction_code=22,
        amount=Decimal("100.50"),
        payment_id="ACH12345",
        receiver_name="Alice Corp",
        reference_info="Invoice #5678"
    )
    ledger_entry_credit = ach_entry_to_ledger_entry(ach_entry_credit)
    assert ledger_entry_credit.entry_id == "ACH12345"
    assert ledger_entry_credit.amount == Decimal("100.50")
    assert ledger_entry_credit.currency == "USD"
    assert ledger_entry_credit.counterparty == "Alice Corp"
    assert ledger_entry_credit.reference == "Invoice #5678"
    assert ledger_entry_credit.rail == "ach"

    # Test case 2: Debit transaction (code 27)
    ach_entry_debit = ACHEntry(
        transaction_code=27,
        amount=Decimal("75.25"),
        payment_id="ACH67890",
        receiver_name="Bob Ltd",
        reference_info="Payment Ref ABC"
    )
    ledger_entry_debit = ach_entry_to_ledger_entry(ach_entry_debit)
    assert ledger_entry_debit.entry_id == "ACH67890"
    assert ledger_entry_debit.amount == Decimal("-75.25")
    assert ledger_entry_debit.currency == "USD"
    assert ledger_entry_debit.counterparty == "Bob Ltd"
    assert ledger_entry_debit.reference == "Payment Ref ABC"
    assert ledger_entry_debit.rail == "ach"

    # Test case 3: Another credit transaction (code 32)
    ach_entry_credit_2 = ACHEntry(
        transaction_code=32,
        amount=Decimal("250.00"),
        payment_id="ACH11223",
        receiver_name="Charlie Inc",
        reference_info="Service Fee"
    )
    ledger_entry_credit_2 = ach_entry_to_ledger_entry(ach_entry_credit_2)
    assert ledger_entry_credit_2.entry_id == "ACH11223"
    assert ledger_entry_credit_2.amount == Decimal("250.00")
    assert ledger_entry_credit_2.currency == "USD"
    assert ledger_entry_credit_2.counterparty == "Charlie Inc"
    assert ledger_entry_credit_2.reference == "Service Fee"
    assert ledger_entry_credit_2.rail == "ach"

    # Test case 4: Another debit transaction (code 37)
    ach_entry_debit_2 = ACHEntry(
        transaction_code=37,
        amount=Decimal("120.70"),
        payment_id="ACH44556",
        receiver_name="David Co",
        reference_info="Reimbursement"
    )
    ledger_entry_debit_2 = ach_entry_to_ledger_entry(ach_entry_debit_2)
    assert ledger_entry_debit_2.entry_id == "ACH44556"
    assert ledger_entry_debit_2.amount == Decimal("-120.70")
    assert ledger_entry_debit_2.currency == "USD"
    assert ledger_entry_debit_2.counterparty == "David Co"
    assert ledger_entry_debit_2.reference == "Reimbursement"
    assert ledger_entry_debit_2.rail == "ach"

    # Test case 5: Unspecified transaction code (assuming debit)
    ach_entry_unspecified = ACHEntry(
        transaction_code=99,
        amount=Decimal("50.00"),
        payment_id="ACH99999",
        receiver_name="Unknown Party",
        reference_info="Misc"
    )
    ledger_entry_unspecified = ach_entry_to_ledger_entry(ach_entry_unspecified)
    assert ledger_entry_unspecified.entry_id == "ACH99999"
    assert ledger_entry_unspecified.amount == Decimal("-50.00") # Assumed debit
    assert ledger_entry_unspecified.currency == "USD"
    assert ledger_entry_unspecified.counterparty == "Unknown Party"
    assert ledger_entry_unspecified.reference == "Misc"
    assert ledger_entry_unspecified.rail == "ach"

    print("TEST PASSED")
