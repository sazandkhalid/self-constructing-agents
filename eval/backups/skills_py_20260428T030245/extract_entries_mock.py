# skill: extract_entries_mock
# version: 1
# tags: what, function, parser, used, extract
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-28T02:59:14.622098+00:00
# decaying: false
# compliance_warn: skill accesses financial/PII data without an audit hook
def extract_entries_mock(xml_string: str) -> list[dict[str, any]]:
    """
    Mock function to extract ledger entries from a camt.053 bank statement XML string.
    This is a placeholder and should be replaced with a proper ISO 20022 XML parser.
    """
    # In a real implementation, this would parse the XML and extract structured data.
    # For demonstration, we'll return a dummy list of entries.
    # Example of expected output structure:
    # [
    #     {
    #         "entry_id": "unique_entry_id_1",
    #         "amount": Decimal("100.50"),
    #         "currency": "USD",
    #         "counterparty": "Example Corp",
    #         "reference": "REF12345",
    #         "rail": "iso20022"
    #     },
    #     {
    #         "entry_id": "unique_entry_id_2",
    #         "amount": Decimal("-50.25"),
    #         "currency": "EUR",
    #         "counterparty": "Another Ltd",
    #         "reference": "REF67890",
    #         "rail": "iso20022"
    #     }
    # ]
    print("Note: Using mock data for extract_entries_mock.")
    return [
        {
            "entry_id": "ENT123",
            "amount": 1000.50,
            "currency": "USD",
            "counterparty": "Merchant A",
            "reference": "PAYMENTREF001",
            "rail": "iso20022"
        },
        {
            "entry_id": "ENT124",
            "amount": -250.75,
            "currency": "EUR",
            "counterparty": "Customer B",
            "reference": "INVOICE1002",
            "rail": "iso20022"
        }
    ]

if __name__ == "__main__":
    # Mock XML string (not used by the mock function, but illustrative)
    mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
        <BkToCstmrStmt>
            <Stmt>
                <Id>statement_id_123</Id>
                <Acct>
                    <IBAN>CH9300762011623852957</IBAN>
                </Acct>
                <Bal>
                    <CdtDbtInd>DBit</CdtDbtInd>
                    <Amt Ccy="USD">1000.50</Amt>
                    <Tp>
                        <CdOrPrtry>
                            <Cd>OPBD</Cd>
                        </CdOrPrtry>
                    </Tp>
                    <Dt>2023-01-01</Dt>
                </Bal>
                <Ntry>
                    <Amt Ccy="USD">1000.50</Amt>
                    <CdtDbtInd>CRDT</CdtDbtInd>
                    <ValDt>
                        <Dt>2023-01-01</Dt>
                    </ValDt>
                    <DbtrNm>Merchant A</DbtrNm>
                    <RmtInf>
                        <UETR>a1b2c3d4e5f67890</UETR>
                    </RmtInf>
                </Ntry>
                <Ntry>
                    <Amt Ccy="EUR">-250.75</Amt>
                    <CdtDbtInd>DBIT</CdtDbtInd>
                    <ValDt>
                        <Dt>2023-01-02</Dt>
                    </ValDt>
                    <CdtrNm>Customer B</CdtrNm>
                    <RmtInf>
                        <UETR>f6e5d4c3b2a10987</UETR>
                    </RmtInf>
                </Ntry>
            </Stmt>
        </BkToCstmrStmt>
    </Document>
    """

    extracted_data = extract_entries_mock(mock_xml)
    assert isinstance(extracted_data, list)
    assert len(extracted_data) == 2
    assert extracted_data[0]["entry_id"] == "ENT123"
    assert extracted_data[0]["amount"] == 1000.50
    assert extracted_data[0]["currency"] == "USD"
    assert extracted_data[0]["counterparty"] == "Merchant A"
    assert extracted_data[0]["reference"] == "PAYMENTREF001"
    assert extracted_data[0]["rail"] == "iso20022"
    assert extracted_data[1]["entry_id"] == "ENT124"
    assert extracted_data[1]["amount"] == -250.75
    assert extracted_data[1]["currency"] == "EUR"
    assert extracted_data[1]["counterparty"] == "Customer B"
    assert extracted_data[1]["reference"] == "INVOICE1002"
    assert extracted_data[1]["rail"] == "iso20022"
    print("TEST PASSED")
