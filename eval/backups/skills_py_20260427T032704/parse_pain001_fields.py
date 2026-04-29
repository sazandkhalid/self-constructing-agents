# skill: parse_pain001_fields
# version: 1
# tags: parse, this, pain, extract, party
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T23:55:18.505912+00:00
# decaying: false
# protocol: iso20022
# rail: swift_mx
# audit_required: true
# protocol: iso20022
# rail: swift_mx
# audit_required: true
def parse_pain001_fields(xml_string: str) -> dict:
    """
    Parses a pain.001 XML string and extracts party and transaction fields.
    """
    import xml.etree.ElementTree as ET

    ns = {
        'pain': 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.09'
    }

    root = ET.fromstring(xml_string)

    fields = {}

    # Message ID
    msg_id_elem = root.find('.//pain:MsgId', ns)
    if msg_id_elem is not None:
        fields['msg_id'] = msg_id_elem.text

    # End to End ID
    e2e_id_elem = root.find('.//pain:EndToEndId', ns)
    if e2e_id_elem is not None:
        fields['e2e_id'] = e2e_id_elem.text

    # Debtor Name and Country
    debtor_nm_elem = root.find('.//pain:Dbtr/pain:Nm', ns)
    if debtor_nm_elem is not None:
        fields['debtor_name'] = debtor_nm_elem.text
    debtor_country_elem = root.find('.//pain:Dbtr/pain:PstlAdr/pain:Ctry', ns)
    if debtor_country_elem is not None:
        fields['debtor_country'] = debtor_country_elem.text

    # Debtor IBAN
    debtor_iban_elem = root.find('.//pain:DbtrAcct/pain:Id/pain:IBAN', ns)
    if debtor_iban_elem is not None:
        fields['debtor_iban'] = debtor_iban_elem.text

    # Creditor Name and Country
    creditor_nm_elem = root.find('.//pain:Cdtr/pain:Nm', ns)
    if creditor_nm_elem is not None:
        fields['creditor_name'] = creditor_nm_elem.text
    creditor_country_elem = root.find('.//pain:Cdtr/pain:PstlAdr/pain:Ctry', ns)
    if creditor_country_elem is not None:
        fields['creditor_country'] = creditor_country_elem.text

    # Creditor IBAN
    creditor_iban_elem = root.find('.//pain:CdtrAcct/pain:Id/pain:IBAN', ns)
    if creditor_iban_elem is not None:
        fields['creditor_iban'] = creditor_iban_elem.text

    # Creditor BIC
    creditor_bic_elem = root.find('.//pain:CdtrAgt/pain:FinInstnId/pain:BICFI', ns)
    if creditor_bic_elem is not None:
        fields['creditor_bic'] = creditor_bic_elem.text

    # Amount and Currency
    instdAmt_elem = root.find('.//pain:Amt/pain:InstdAmt', ns)
    if instdAmt_elem is not None:
        fields['amount'] = instdAmt_elem.text
        fields['currency'] = instdAmt_elem.get('Ccy')

    # Remittance Info
    ustrd_elem = root.find('.//pain:RmtInf/pain:Ustrd', ns)
    if ustrd_elem is not None:
        fields['remittance_info'] = ustrd_elem.text
    else: # Fallback for other remittance info types if needed in future
        strd_elem = root.find('.//pain:RmtInf/pain:Strd', ns)
        if strd_elem is not None:
            fields['remittance_info'] = strd_elem.text # This might need more complex handling

    return fields

if __name__ == "__main__":
    xml = '<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"><CstmrCdtTrfInitn><GrpHdr><MsgId>MERIDIAN-20251119-001</MsgId></GrpHdr><PmtInf><Dbtr><Nm>Meridian Ltd</Nm><PstlAdr><Ctry>GB</Ctry></PstlAdr></Dbtr><DbtrAcct><Id><IBAN>GB29NWBK60161331926819</IBAN></Id></DbtrAcct><CdtTrfTxInf><EndToEndId>E2E-INV-2025-0847</EndToEndId><Amt><InstdAmt Ccy="EUR">47832.50</InstdAmt></Amt><CdtrAgt><FinInstnId><BICFI>DEUTDEDB</BICFI></FinInstnId></CdtrAgt><Cdtr><Nm>Fischer GmbH</Nm><PstlAdr><Ctry>DE</Ctry></PstlAdr></Cdtr><CdtrAcct><Id><IBAN>DE89370400440532013000</IBAN></Id></CdtrAcct><RmtInf><Ustrd>Invoice INV-2025-0847</Ustrd></RmtInf></CdtTrfTxInf></PmtInf></CstmrCdtTrfInitn></Document>'
    result = parse_pain001_fields(xml)
    assert isinstance(result, dict)
    assert result.get("msg_id") == "MERIDIAN-20251119-001"
    assert result.get("creditor_bic") == "DEUTDEDB"
    assert result.get("amount") == "47832.50" or result.get("amount") == 47832.50
    assert result.get("e2e_id") == "E2E-INV-2025-0847"
    assert result.get("debtor_name") == "Meridian Ltd"
    assert result.get("debtor_iban") == "GB29NWBK60161331926819"
    assert result.get("debtor_country") == "GB"
    assert result.get("creditor_name") == "Fischer GmbH"
    assert result.get("creditor_iban") == "DE89370400440532013000"
    assert result.get("creditor_country") == "DE"
    assert result.get("currency") == "EUR"
    assert result.get("remittance_info") == "Invoice INV-2025-0847"
    print("TEST PASSED")
