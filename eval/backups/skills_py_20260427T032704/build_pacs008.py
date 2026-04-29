# skill: build_pacs008
# version: 1
# tags: build, pacs, message, write, python
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-24T00:05:13.052739+00:00
# decaying: false
# protocol: iso20022
# rail: swift_mx
# audit_required: true
# protocol: iso20022
# rail: swift_mx
# audit_required: true
def build_pacs008(pain001_fields: dict, settlement_rate: float) -> str:
    """
    Builds a pacs.008.001.08 XML message string.
    """
    import xml.etree.ElementTree as ET

    # Define namespaces
    ns_pacs008 = "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"
    ns_xsi = "http://www.w3.org/2001/XMLSchema-instance"
    ns_xml = "http://www.w3.org/XML/1998/namespace"

    # Create the root element with namespaces
    pacs008 = ET.Element(f"{{{ns_pacs008}}}Document", {
        "xmlns": ns_pacs008,
        f"{{{ns_xsi}}}schemaLocation": f"{ns_pacs008} {ns_pacs008}",
        f"{{{ns_xml}}}lang": "EN"
    })

    # GrpHdr
    grphdr = ET.SubElement(pacs008, f"{{{ns_pacs008}}}GrpHdr")
    ET.SubElement(grphdr, f"{{{ns_pacs008}}}MsgId").text = "SWIFT-" + pain001_fields.get("msg_id", "")
    ET.SubElement(grphdr, f"{{{ns_pacs008}}}NbOfTxs").text = "1"

    # SttlmInf
    sttlminf = ET.SubElement(grphdr, f"{{{ns_pacs008}}}SttlmInf")
    ET.SubElement(sttlminf, f"{{{ns_pacs008}}}SttlmMtd").text = "CLSS"

    # CdtTrfTxInf
    cdttftxinf = ET.SubElement(pacs008, f"{{{ns_pacs008}}}CdtTrfTxInf")

    # PmtId
    pmtid = ET.SubElement(cdttftxinf, f"{{{ns_pacs008}}}PmtId")
    ET.SubElement(pmtid, f"{{{ns_pacs008}}}EndToEndId").text = pain001_fields.get("e2e_id", "")

    # IntrBkSttlmAmt
    intr_bk_sttlm_amt = ET.SubElement(cdttftxinf, f"{{{ns_pacs008}}}IntrBkSttlmAmt")
    intr_bk_sttlm_amt.set("Ccy", pain001_fields.get("currency", "EUR"))
    intr_bk_sttlm_amt.text = str(pain001_fields.get("amount", "0.00"))

    ET.SubElement(cdttftxinf, f"{{{ns_pacs008}}}ChrgBr").text = "SHA"

    # DbtrAgt
    dbtragt = ET.SubElement(cdttftxinf, f"{{{ns_pacs008}}}DbtrAgt")
    dbtragt_bic = ET.SubElement(dbtragt, f"{{{ns_pacs008}}}FinInstnId")
    ET.SubElement(dbtragt_bic, f"{{{ns_pacs008}}}BIC").text = "NWBKGB2L"

    # Cdtr
    cdtr = ET.SubElement(cdttftxinf, f"{{{ns_pacs008}}}Cdtr")
    ET.SubElement(cdtr, f"{{{ns_pacs008}}}Nm").text = pain001_fields.get("creditor_name", "")

    # CdtrAcct
    cdtracct = ET.SubElement(cdttftxinf, f"{{{ns_pacs008}}}CdtrAcct")
    ET.SubElement(cdtracct, f"{{{ns_pacs008}}}IBAN").text = pain001_fields.get("creditor_iban", "")

    # Convert to string
    return ET.tostring(pacs008, encoding="unicode")

if __name__ == "__main__":
    import xml.etree.ElementTree as ET
    fields = {"msg_id":"MERIDIAN-001","e2e_id":"E2E-INV-2025-0847","creditor_name":"Fischer GmbH","creditor_iban":"DE89370400440532013000","creditor_bic":"DEUTDEDB","currency":"EUR","amount":"47832.50"}
    xml_str = build_pacs008(fields, 0.853)
    
    # Basic assertion for string type and length
    assert isinstance(xml_str, str) and len(xml_str) > 50, f"Expected non-empty string, but got: {xml_str}"
    
    # Assert for EndToEndId
    assert "E2E-INV-2025-0847" in xml_str, f"EndToEndId missing in XML. Snippet: {xml_str[:200]}"
    
    # Assert for MsgId
    # The requirement mentions "SWIFT-" + pain001_fields.get("msg_id","")
    # The test asserts "SWIFT-MERIDIAN-001" OR "MERIDIAN" in xml_str.
    # The first part "SWIFT-MERIDIAN-001" is the correct expected behavior.
    # We'll assert for the complete expected string for clarity and strictness.
    assert "SWIFT-MERIDIAN-001" in xml_str, f"MsgId 'SWIFT-MERIDIAN-001' missing in XML. Snippet: {xml_str[:200]}"
    
    # Further checks for other fields
    assert "Fischer GmbH" in xml_str, "Creditor Name missing"
    assert "DE89370400440532013000" in xml_str, "Creditor IBAN missing"
    assert "EUR" in xml_str and 'Ccy="EUR"' in xml_str, "Currency missing or incorrect format"
    assert "47832.50" in xml_str, "Amount missing"
    assert "CLSS" in xml_str, "SttlmMtd missing"
    assert "NWBKGB2L" in xml_str, "DbtrAgt BIC missing"
    assert "SHA" in xml_str, "ChrgBr missing"

    print("TEST PASSED")
