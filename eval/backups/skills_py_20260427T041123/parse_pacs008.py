# skill: parse_pacs008
# version: 1
# tags: have, seen, parse_pacs008, extract_statement_entries, both
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-27T04:10:39.204198+00:00
# decaying: false
# compliance_warn: skill accesses financial/PII data without an audit hook
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass, asdict

# Assume these constants are defined in messages.py
# For demonstration, we'll define them here.
PACS_008_001_08 = "pacs.008.001.08"
CAMT_053_001_02 = "camt.053.001.02"

# Mock parser functions (replace with actual imports from parser.py)
def parse_pacs008(xml_string: str) -> Dict[str, Any]:
    """Mock parser for pacs.008."""
    # In a real scenario, this would parse the XML and return a structured dict or dataclass.
    # For simplicity, we'll return a dummy dict.
    root = ET.fromstring(xml_string)
    msg_id_elem = root.find(".//{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}MsgId")
    amount_elem = root.find(".//{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}InstdAmt")
    
    if msg_id_elem is not None and amount_elem is not None:
        return {
            "message_id": msg_id_elem.text,
            "amount": amount_elem.text,
            "currency": amount_elem.get("Ccy")
        }
    else:
        raise ValueError("Could not parse pacs.008 required fields.")

def extract_statement_entries(xml_string: str) -> Dict[str, Any]:
    """Mock parser for camt.053."""
    # In a real scenario, this would parse the XML and return a structured dict or dataclass.
    # For simplicity, we'll return a dummy dict.
    root = ET.fromstring(xml_string)
    stmt_id_elem = root.find(".//{urn:iso:std:iso:20022:tech:xsd:camt.053.001.02}StmtId")
    entries = []
    for entry in root.findall(".//{urn:iso:std:iso:20022:tech:xsd:camt.053.001.02}Ntry"):
        ref_elem = entry.find(".//{urn:iso:std:iso:20022:tech:xsd:camt.053.001.02}NtryRef")
        amt_elem = entry.find(".//{urn:iso:std:iso:20022:tech:xsd:camt.053.001.02}Amt")
        if ref_elem is not None and amt_elem is not None:
            entries.append({
                "entry_reference": ref_elem.text,
                "amount": amt_elem.text,
                "currency": amt_elem.get("Ccy")
            })
    
    if stmt_id_elem is not None:
        return {
            "statement_id": stmt_id_elem.text,
            "entries": entries
        }
    else:
        raise ValueError("Could not parse camt.053 required fields.")

# Registry of parsers
ISO20022_PARSER_REGISTRY = {
    PACS_008_001_08: parse_pacs008,
    CAMT_053_001_02: extract_statement_entries,
    # Add other parsers here as they are defined
}

def get_message_family(msg_type: str) -> Literal["pacs", "camt", "pain", "unknown"]:
    """Determines the family of an ISO 20022 message type."""
    if msg_type.startswith("pacs."):
        return "pacs"
    elif msg_type.startswith("camt."):
        return "camt"
    elif msg_type.startswith("pain."):
        return "pain"
    else:
        return "unknown"

def parse_iso20022_message(xml_string: str, msg_type: str) -> Dict[str, Any]:
    """
    Parses an ISO 20022 message dynamically using a registry.

    Args:
        xml_string: The XML string of the ISO 20022 message.
        msg_type: The ISO 20022 message type string (e.g., "pacs.008.001.08").

    Returns:
        A dictionary with keys: msg_type, family, payload, and parse_error.
        Payload will be a dictionary representation of the parsed data.
    """
    payload = None
    parse_error = None
    family = get_message_family(msg_type)

    parser_func = ISO20022_PARSER_REGISTRY.get(msg_type)

    if parser_func:
        try:
            parsed_data = parser_func(xml_string)
            # Ensure payload is always a dict, even if parser returns dataclass
            if dataclass in type(parsed_data).__dict__.values():
                payload = asdict(parsed_data)
            else:
                payload = parsed_data
        except Exception as e:
            parse_error = f"Error parsing {msg_type}: {e}"
    else:
        parse_error = f"Unsupported message type: {msg_type}"

    return {
        "msg_type": msg_type,
        "family": family,
        "payload": payload,
        "parse_error": parse_error,
    }

if __name__ == "__main__":
    # Test case 1: pacs.008
    pacs_xml = """
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
      <FIToFICstmrCdtTrf>
        <GrpHdr>
          <MsgId>MSG123</MsgId>
          <CreDtTm>2023-10-27T10:00:00Z</CreDtTm>
        </GrpHdr>
        <CdtTrfTxInf>
          <PmtId>
            <EndToEndId>E2E12345</EndToEndId>
          </PmtId>
          <Amt>
            <InstdAmt Ccy="EUR">1234.56</InstdAmt>
          </Amt>
          <CdtrAgt>
            <FinInstnId>
              <BIC>CREDDEFFXXX</BIC>
            </FinInstnId>
          </CdtrAgt>
          <DbtrAgt>
            <FinInstnId>
              <BIC>DEBDCHHHXXX</BIC>
            </FinInstnId>
          </DbtrAgt>
        </CdtTrfTxInf>
      </FIToFICstmrCdtTrf>
    </Document>
    """
    result_pacs = parse_iso20022_message(pacs_xml, PACS_008_001_08)
    assert result_pacs["msg_type"] == PACS_008_001_08
    assert result_pacs["family"] == "pacs"
    assert result_pacs["payload"]["message_id"] == "MSG123"
    assert result_pacs["payload"]["amount"] == "1234.56"
    assert result_pacs["payload"]["currency"] == "EUR"
    assert result_pacs["parse_error"] is None

    # Test case 2: camt.053
    camt_xml = """
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
      <BkToCstmrDbtCdtNtfctn>
        <GrpHdr>
          <MsgId>CAMTMSG789</MsgId>
          <CreDtTm>2023-10-27T10:00:00Z</CreDtTm>
        </GrpHdr>
        <Ntfctn>
          <Header>
            <StmtId>STMTID987</StmtId>
            <AccOwnr>
              <Id>
                <IBAN>CH9300762011627320090</IBAN>
              </Id>
            </AccOwnr>
          </Header>
          <BankTransactionCode>
            <DomnCd>FundsClosBal</DomnCd>
          </BankTransactionCode>
          <Ntry>
            <Amt Ccy="GBP">500.00</Amt>
            <NtryRef>REF001</NtryRef>
            <AddtlNtryInf>Incoming payment</AddtlNtryInf>
          </Ntry>
          <Ntry>
            <Amt Ccy="GBP">-75.50</Amt>
            <NtryRef>REF002</NtryRef>
            <AddtlNtryInf>Outgoing fee</AddtlNtryInf>
          </Ntry>
        </Ntfctn>
      </BkToCstmrDbtCdtNtfctn>
    </Document>
    """
    result_camt = parse_iso20022_message(camt_xml, CAMT_053_001_02)
    assert result_camt["msg_type"] == CAMT_053_001_02
    assert result_camt["family"] == "camt"
    assert result_camt["payload"]["statement_id"] == "STMTID987"
    assert len(result_camt["payload"]["entries"]) == 2
    assert result_camt["payload"]["entries"][0]["entry_reference"] == "REF001"
    assert result_camt["payload"]["entries"][0]["amount"] == "500.00"
    assert result_camt["payload"]["entries"][0]["currency"] == "GBP"
    assert result_camt["payload"]["entries"][1]["entry_reference"] == "REF002"
    assert result_camt["payload"]["entries"][1]["amount"] == "-75.50"
    assert result_camt["parse_error"] is None

    # Test case 3: Unknown message type
    unknown_xml = "<Document>Some random XML</Document>"
    result_unknown = parse_iso20022_message(unknown_xml, "unknown.message.type")
    assert result_unknown["msg_type"] == "unknown.message.type"
    assert result_unknown["family"] == "unknown"
    assert result_unknown["payload"] is None
    assert "Unsupported message type: unknown.message.type" in result_unknown["parse_error"]

    # Test case 4: Parser error
    invalid_pacs_xml = """
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
      <FIToFICstmrCdtTrf>
        <GrpHdr>
          <MsgId>MSG_NO_AMOUNT</MsgId>
        </GrpHdr>
      </FIToFICstmrCdtTrf>
    </Document>
    """
    result_invalid_pacs = parse_iso20022_message(invalid_pacs_xml, PACS_008_001_08)
    assert result_invalid_pacs["msg_type"] == PACS_008_001_08
    assert result_invalid_pacs["family"] == "pacs"
    assert result_invalid_pacs["payload"] is None
    assert "Error parsing pacs.008" in result_invalid_pacs["parse_error"]

    print("TEST PASSED")
