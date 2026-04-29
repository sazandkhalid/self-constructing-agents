"""
NACHA ACH file format utilities.
ACH is the primary US domestic batch payment rail.
"""

from dataclasses import dataclass, field
from typing import List
from datetime import date
import random, string

@dataclass
class ACHEntry:
    routing_number: str      # 9 digits
    account_number: str
    amount_cents: int        # in cents
    individual_name: str
    trace_number: str = ""
    transaction_code: int = 22   # 22=checking credit, 27=checking debit

    def __post_init__(self):
        if not self.trace_number:
            self.trace_number = "".join(random.choices(string.digits, k=15))
        if len(self.routing_number) != 9:
            raise ValueError("routing_number must be exactly 9 digits")

@dataclass
class ACHBatch:
    company_name: str
    company_id: str
    entries: List[ACHEntry] = field(default_factory=list)
    sec_code: str = "PPD"   # PPD, CCD, CTX, WEB

    @property
    def total_debit_cents(self) -> int:
        return sum(e.amount_cents for e in self.entries
                   if e.transaction_code in (27, 37, 47))

    @property
    def total_credit_cents(self) -> int:
        return sum(e.amount_cents for e in self.entries
                   if e.transaction_code in (22, 32, 42))

def format_ach_amount(cents: int) -> str:
    """Format cents as NACHA 10-digit zero-padded amount string."""
    return str(cents).zfill(10)

def validate_routing_number(routing: str) -> bool:
    """Validate ABA routing number using checksum algorithm."""
    if not routing.isdigit() or len(routing) != 9:
        return False
    d = [int(c) for c in routing]
    checksum = (3*(d[0]+d[3]+d[6]) + 7*(d[1]+d[4]+d[7]) + (d[2]+d[5]+d[8])) % 10
    return checksum == 0

def build_ach_file(batch: ACHBatch, effective_date: date) -> str:
    """Build a minimal NACHA-formatted ACH file string."""
    lines = []
    lines.append(f"101 {batch.company_id[:9].ljust(9)}{'DEST'.ljust(23)}{date.today().strftime('%y%m%d')}")
    lines.append(f"5220{batch.company_name[:16].ljust(16)}{batch.company_id[:10].ljust(10)}{batch.sec_code}{effective_date.strftime('%y%m%d')}")
    for entry in batch.entries:
        lines.append(f"6{entry.transaction_code:02d}{entry.routing_number}{entry.account_number[:17].ljust(17)}{format_ach_amount(entry.amount_cents)}{entry.individual_name[:22].ljust(22)}{entry.trace_number[:15]}")
    lines.append(f"8220{len(batch.entries):06d}{batch.total_debit_cents:012d}{batch.total_credit_cents:012d}")
    lines.append(f"9{'':23}{len(batch.entries):06d}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Known valid ABA routing numbers
    assert validate_routing_number("021000021")  # JPMorgan Chase
    assert validate_routing_number("011000138")  # BofA
    assert not validate_routing_number("000000001")  # invalid checksum
    assert not validate_routing_number("12345")
    assert format_ach_amount(150000) == "0000150000"
    entry = ACHEntry(routing_number="021000021", account_number="12345678",
                     amount_cents=10000, individual_name="Test User")
    assert len(entry.trace_number) == 15
    print("TEST PASSED")
