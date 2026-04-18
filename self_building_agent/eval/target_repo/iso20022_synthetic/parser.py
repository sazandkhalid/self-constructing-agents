"""
Minimal ISO 20022 XML parser.
Extracts structured fields from MX message envelopes.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

NS = {
    "pacs008": "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08",
    "camt053": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.08",
    "pain001": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09",
}

@dataclass
class CreditTransfer:
    msg_id: str
    end_to_end_id: str
    amount: float
    currency: str
    debtor_name: Optional[str]
    creditor_name: Optional[str]
    creditor_iban: Optional[str]
    remittance_info: Optional[str]

def parse_pacs008(xml_string: str) -> Optional[CreditTransfer]:
    """Parse a pacs.008 FI-to-FI credit transfer message."""
    try:
        root = ET.fromstring(xml_string)
        ns = NS["pacs008"]
        def find(tag):
            el = root.find(f".//{{{ns}}}{tag}")
            return el.text.strip() if el is not None and el.text else None
        amt_el = root.find(f".//{{{ns}}}IntrBkSttlmAmt")
        currency = amt_el.get("Ccy", "USD") if amt_el is not None else "USD"
        # Nested name fields need their own namespace path
        def find_nested(parent_tag, child_tag):
            parent = root.find(f".//{{{ns}}}{parent_tag}")
            if parent is None:
                return None
            child = parent.find(f"{{{ns}}}{child_tag}")
            return child.text.strip() if child is not None and child.text else None
        return CreditTransfer(
            msg_id=find("MsgId") or "",
            end_to_end_id=find("EndToEndId") or "",
            amount=float(amt_el.text.strip() if amt_el is not None and amt_el.text else 0),
            currency=currency,
            debtor_name=find_nested("Dbtr", "Nm"),
            creditor_name=find_nested("Cdtr", "Nm"),
            creditor_iban=find("IBAN"),
            remittance_info=find("Ustrd"),
        )
    except ET.ParseError:
        return None

def extract_statement_entries(xml_string: str) -> list:
    """Extract entries from a camt.053 bank statement."""
    try:
        root = ET.fromstring(xml_string)
        ns = NS["camt053"]
        entries = []
        for ntry in root.findall(f".//{{{ns}}}Ntry"):
            def fv(tag):
                el = ntry.find(f".//{{{ns}}}{tag}")
                return el.text.strip() if el is not None and el.text else None
            entries.append({
                "amount": fv("Amt"),
                "credit_debit": fv("CdtDbtInd"),
                "booking_date": fv("BookgDt/Dt"),
                "end_to_end_id": fv("EndToEndId"),
                "remittance": fv("Ustrd"),
            })
        return entries
    except ET.ParseError:
        return []


if __name__ == "__main__":
    xml = """<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
  <FIToFICstmrCdtTrf>
    <GrpHdr><MsgId>MSG001</MsgId></GrpHdr>
    <CdtTrfTxInf>
      <PmtId><EndToEndId>E2E001</EndToEndId></PmtId>
      <IntrBkSttlmAmt Ccy="EUR">1234.56</IntrBkSttlmAmt>
      <Dbtr><Nm>Alice</Nm></Dbtr>
      <Cdtr><Nm>Bob</Nm></Cdtr>
    </CdtTrfTxInf>
  </FIToFICstmrCdtTrf>
</Document>"""
    ct = parse_pacs008(xml)
    assert ct is not None
    assert ct.msg_id == "MSG001"
    assert ct.amount == 1234.56
    assert ct.currency == "EUR"
    assert ct.debtor_name == "Alice"
    assert parse_pacs008("not xml") is None
    print("TEST PASSED")
