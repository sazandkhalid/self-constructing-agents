# skill: build_pacs002_acceptance
# version: 1
# tags: build, pacs, payment, status, report
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T23:57:06.960375+00:00
# decaying: false
# protocol: iso20022
# rail: swift_mx
# audit_required: true
# protocol: iso20022
# rail: swift_mx
# audit_required: true
def build_pacs002_acceptance(original_msg_id: str, original_e2e_id: str, original_tx_id: str, settlement_amount: float, settlement_currency: str, settlement_date: str) -> str:
    """
    Constructs a pacs.002.001.10 payment status report XML string for acceptance.
    """
    import xml.etree.ElementTree as ET

    # Define the XML structure and namespaces
    # Namespace for pacs.002.001.10
    ns = {
        'ns0': 'urn:iso:std:iso:20022:tech:xsd:pacs.002.001.10'
    }
    ET.register_namespace('', ns['ns0'])

    # Root element
    root = ET.Element("Document", ns)

    # PaymentStatusReportV10
    payment_status_report = ET.SubElement(root, "n0:PaymentStatusReportV10", ns)

    # Group Header
    grpHdr = ET.SubElement(payment_status_report, "n0:GrpHdr")
    msg_id = ET.SubElement(grpHdr, "n0:MsgId")
    msg_id.text = f"ACK-{original_msg_id}"
    cre_dt_tm = ET.SubElement(grpHdr, "n0:CreDtTm")
    # For simplicity, using today's date in the correct format, but a real implementation
    # would use the current date and time.
    from datetime import datetime
    cre_dt_tm.text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    msg_func_h = ET.SubElement(grpHdr, "n0:MsgFuncHdr")
    msg_func_h.text = "STAT"
    nb_of_txns = ET.SubElement(grpHdr, "n0:NbOfTxs")
    nb_of_txns.text = "1"

    # Detail of Transaction
    tx_inf_and_sts = ET.SubElement(payment_status_report, "n0:TxInfAndSts")
    tx_st_l = ET.SubElement(tx_inf_and_sts, "n0:TxSts")
    tx_st_l.text = "ACCP"
    orgnl_end_to_end_id = ET.SubElement(tx_inf_and_sts, "n0:OrgnlEndToEndId")
    orgnl_end_to_end_id.text = original_e2e_id
    orgnl_tx_id = ET.SubElement(tx_inf_and_sts, "n0:OrgnlTxId")
    orgnl_tx_id.text = original_tx_id

    # Settlement Information
    sttlm_inf = ET.SubElement(tx_inf_and_sts, "n0:SttlmInf")
    sttlm_dt = ET.SubElement(sttlm_inf, "n0:SttlmDt")
    sttlm_dt.text = settlement_date
    sttlm_amt = ET.SubElement(sttlm_inf, "n0:SttlmAmt")
    # Format settlement amount to have two decimal places
    sttlm_amt.text = f"{settlement_amount:.2f}"
    sttlm_cur = ET.SubElement(sttlm_inf, "n0:SttlmCcy")
    sttlm_cur.text = settlement_currency

    # Convert the ElementTree to a string
    # Add the XML declaration and pretty print
    xml_string = ET.tostring(root, encoding='unicode', method='xml')
    # Manually add XML declaration as ET.tostring does not include it by default
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_string

if __name__ == "__main__":
    result = build_pacs002_acceptance("MERIDIAN-001","E2E-INV-2025-0847","TXN-001",47832.50,"EUR","2025-11-19")
    assert isinstance(result, str) and len(result) > 50, f"must return non-empty XML string, got: {result}"
    assert "ACCP" in result, f"TxSts ACCP missing: {result[:200]}"
    assert "E2E-INV-2025-0847" in result, "OrgnlEndToEndId missing"
    assert "ACK-MERIDIAN-001" in result, "ACK prefix missing"
    assert "47832.50" in result, "Settlement amount formatting missing"
    assert "EUR" in result, "Settlement currency missing"
    assert "2025-11-19" in result, "Settlement date missing"
    print("TEST PASSED")
