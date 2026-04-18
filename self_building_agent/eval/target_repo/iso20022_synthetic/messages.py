"""
ISO 20022 message type registry.
Covers pacs (payments clearing), camt (cash management), pain (payment initiation).
"""

PACS_008 = "pacs.008.001.08"   # FI to FI customer credit transfer
PACS_009 = "pacs.009.001.08"   # FI to FI financial institution credit transfer
PACS_002 = "pacs.002.001.10"   # FI to FI payment status report
CAMT_053 = "camt.053.001.08"   # bank to customer statement
CAMT_054 = "camt.054.001.08"   # bank to customer debit credit notification
PAIN_001 = "pain.001.001.09"   # customer credit transfer initiation
PAIN_002 = "pain.002.001.10"   # customer payment status report

MESSAGE_FAMILIES = {
    "pacs": "Payments Clearing and Settlement",
    "camt": "Cash Management",
    "pain": "Payment Initiation",
}

def get_family(msg_type: str) -> str:
    prefix = msg_type.split(".")[0]
    return MESSAGE_FAMILIES.get(prefix, "Unknown")

def is_credit_transfer(msg_type: str) -> bool:
    return msg_type in (PACS_008, PACS_009, PAIN_001)

def is_status_report(msg_type: str) -> bool:
    return msg_type in (PACS_002, PAIN_002)


if __name__ == "__main__":
    assert get_family(PACS_008) == "Payments Clearing and Settlement"
    assert get_family(CAMT_053) == "Cash Management"
    assert get_family("unknown.001") == "Unknown"
    assert is_credit_transfer(PACS_008)
    assert not is_credit_transfer(PACS_002)
    assert is_status_report(PAIN_002)
    print("TEST PASSED")
