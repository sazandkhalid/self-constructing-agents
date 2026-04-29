---
name: iso20022_message_parser_skill
tags:
- iso20022
- parser
- abstraction
- dispatcher
trigger: when needing to parse a generic ISO 20022 message of a known type.
type: pattern
version: 1
success_count: 6
fail_count: 0
---
---
# ISO 20022 Message Parser Skill
## Purpose
This skill provides a unified interface for parsing various ISO 20022 messages. It dispatches to specific parsers based on the message type and normalizes the output into a consistent dictionary format.
## When to use
Use this skill when you need to parse an ISO 20022 XML message and the specific message type is known. This is useful for scenarios where you want to handle different ISO 20022 message formats (e.g., pacs.008, camt.053) through a single function.
## How to use
1. **Identify the message type:** Determine the `msg_type` string (e.g., "pacs.008", "camt.053").
2. **Provide the XML string:** Pass the ISO 20022 XML message as an `xml_string`.
3. **Call the function:** Invoke `parse_iso20022_message(xml_string, msg_type)`.
4. **Handle the output:** The function returns a dictionary with the following keys:
    - `msg_type`: The original message type string.
    - `family`: The message family (e.g., "pacs", "camt").
    - `payload`: The parsed message content as a dictionary. If parsing fails, this will be `None`.
    - `parse_error`: A string describing any parsing error, or `None` if successful.

This skill assumes the existence of specific parsing functions (e.g., `parse_pacs008`, `extract_statement_entries`) and a way to determine message families, potentially by inspecting message type constants from a `messages.py` file.

---PY SKILL---
import re
from typing import Dict, Any, Optional, Literal

# Assume these functions exist and are imported
# from .parsers import parse_pacs008, extract_statement_entries
# Assume messages.py has constants like:
# PACS_008_001_08 = "pacs.008.001.08"
# CAMT_053_001_02 = "camt.053.001.02"

# Mock implementations for demonstration purposes
def parse_pacs008(xml_string: str) -> Dict[str, Any]:
    # Placeholder for actual pacs.008 parsing logic
    print("Parsing pacs.008")
    if "<MsgId>MSG123</MsgId>" in xml_string:
        return {"message_id": "MSG123", "amount": "100.50"}
    else:
        raise ValueError("Invalid pacs.008 format")

def extract_statement_entries(xml_string: str) -> Dict[str, Any]:
    # Placeholder for actual camt.053 parsing logic
    print("Parsing camt.053")
    if "<StmtId>STMT456</StmtId>" in xml_string:
        return {"statement_id": "STMT456", "entries": [{"entry_ref": "REF789", "amount": "250.75"}]}
    else:
        raise ValueError("Invalid camt.053 format")

def get_message_family(msg_type: str) -> Literal["pacs", "camt", "pain", "unknown"]:
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
    Parses an ISO 20022 message based on its type and returns a normalized dictionary.

    Args:
        xml_string: The XML string of the ISO 20022 message.
        msg_type: The ISO 20022 message type string (e.g., "pacs.008.001.08").

    Returns:
        A dictionary with keys: msg_type, family, payload, and parse_error.
    """
    payload = None
    parse_error = None
    family = get_message_family(msg_type)

    try:
        if msg_type.startswith("pacs.008"):
            payload = parse_pacs008(xml_string)
        elif msg_type.startswith("camt.053"):
            payload = extract_statement_entries(xml_string)
        else:
            parse_error = f"Unsupported message type: {msg_type}"
    except Exception as e:
        parse_error = f"Error parsing {msg_type}: {e}"

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
        <CstmrCdtTrfInit>
            <GrpHdr>
                <MsgId>MSG123</MsgId>
            </GrpHdr>
            <SplmtryData>
                <Envlp>
                    <｝>
                </Envlp>
            </SplmtryData>
        </CstmrCdtTrfInit>
    </Document>
    """
    result_pacs = parse_iso20022_message(pacs_xml, "pacs.008.001.08")
    assert result_pacs["msg_type"] == "pacs.008.001.08"
    assert result_pacs["family"] == "pacs"
    assert result_pacs["payload"]["message_id"] == "MSG123"
    assert result_pacs["payload"]["amount"] == "100.50"
    assert result_pacs["parse_error"] is None

    # Test case 2: camt.053
    camt_xml = """
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
        <BkToCstmrDbtCdtNtfctn>
            <GrpHdr>
                <MsgId>MSG789</MsgId>
            </GrpHdr>
            <Ntfctn>
                <Stmt>
                    <Id>STMT456</Id>
                    <Entry>
                        <NtryRef>REF789</NtryRef>
                        <Amt Ccy="EUR">250.75</Amt>
                    </Entry>
                </Stmt>
            </Ntfctn>
        </BkToCstmrDbtCdtNtfctn>
    </Document>
    """
    result_camt = parse_iso20022_message(camt_xml, "camt.053.001.02")
    assert result_camt["msg_type"] == "camt.053.001.02"
    assert result_camt["family"] == "camt"
    assert result_camt["payload"]["statement_id"] == "STMT456"
    assert result_camt["payload"]["entries"][0]["entry_ref"] == "REF789"
    assert result_camt["payload"]["entries"][0]["amount"] == "250.75"
    assert result_camt["parse_error"] is None

    # Test case 3: Unsupported message type
    unsupported_xml = "<Document>Some XML</Document>"
    result_unsupported = parse_iso20022_message(unsupported_xml, "some.other.type")
    assert result_unsupported["msg_type"] == "some.other.type"
    assert result_unsupported["family"] == "unknown"
    assert result_unsupported["payload"] is None
    assert "Unsupported message type" in result_unsupported["parse_error"]

    # Test case 4: Parsing error in pacs.008
    invalid_pacs_xml = """
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
        <CstmrCdtTrfInit>
            <GrpHdr>
                <MsgId>INVALID_MSG</MsgId>
            </GrpHdr>
        </CstmrCdtTrfInit>
    </Document>
    """
    result_invalid_pacs = parse_iso20022_message(invalid_pacs_xml, "pacs.008.001.08")
    assert result_invalid_pacs["msg_type"] == "pacs.008.001.08"
    assert result_invalid_pacs["family"] == "pacs"
    assert result_invalid_pacs["payload"] is None
    assert "Error parsing pacs.008" in result_invalid_pacs["parse_error"]


    print("TEST PASSED")
---END PY SKILL---

4. ---NEW TASK---
Create a mechanism to discover and load available ISO 20022 parsers dynamically, rather than hardcoding them in `parse_iso20022_message`. This could involve inspecting a directory of parser modules or using a registry pattern.
---END TASK---