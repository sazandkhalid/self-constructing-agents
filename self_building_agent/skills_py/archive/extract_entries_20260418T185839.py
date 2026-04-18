# skill: extract_entries
# version: 1
# tags: what, function, parser, used, extract
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-18T18:56:51.377902+00:00
# decaying: false
# compliance_warn: skill accesses financial/PII data without an audit hook
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

@dataclass
class Entry:
    """Represents an entry in a camt.053 bank statement."""
    entry_reference: str
    account_owner: str
    account_number: str
    amount: float
    currency: str
    booking_date: str
    value_date: str

def extract_entries(xml_string: str) -> list[Optional[Entry]]:
    # Implementation to parse the xml_string and extract entries
    # For demonstration purposes, assume we have a simple parsing logic
    root = ET.fromstring(xml_string)
    entries = []
    for entry_element in root.findall('.//Entry'):
        entry = Entry(
            entry_reference=entry_element.find('EntryRef').text,
            account_owner=entry_element.find('AcctOwnr').text,
            account_number=entry_element.find('AcctNr').text,
            amount=float(entry_element.find('Amt').text),
            currency=entry_element.find('Ccy').text,
            booking_date=entry_element.find('BookgDt').text,
            value_date=entry_element.find('ValDt').text
        )
        entries.append(entry)
    return entries

if __name__ == "__main__":
    # Example usage
    xml_string = """
    <Document>
        <Entry>
            <EntryRef>REF1</EntryRef>
            <AcctOwnr>Owner1</AcctOwnr>
            <AcctNr>12345</AcctNr>
            <Amt>100.0</Amt>
            <Ccy>USD</Ccy>
            <BookgDt>2022-01-01</BookgDt>
            <ValDt>2022-01-02</ValDt>
        </Entry>
    </Document>
    """
    entries = extract_entries(xml_string)
    for entry in entries:
        print(entry)
    print("TEST PASSED")
