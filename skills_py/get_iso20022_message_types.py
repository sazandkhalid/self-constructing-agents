# skill: get_iso20022_message_types
# version: 1
# tags: list, message, type, constants, defined
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-28T03:13:33.745881+00:00
# decaying: false
# protocol: iso20022
# rail: swift_mx
# audit_required: false
# protocol: iso20022
# rail: swift_mx
# audit_required: false
def get_iso20022_message_types():
    """
    Lists all ISO 20022 message type constants with their families and descriptions
    based on the current messages.py file.

    Returns:
        list[dict]: A list of dictionaries, each containing 'constant', 'value', 'family', and 'description'.
    """
    message_types = [
        {"constant": "PACS_008", "value": "pacs.008.001.08", "family": "pacs", "description": "FI to FI customer credit transfer"},
        {"constant": "PACS_009", "value": "pacs.009.001.08", "family": "pacs", "description": "FI to FI credit transfer"},
        {"constant": "CAMT_053", "value": "camt.053.001.02", "family": "camt", "description": "Bank to customer statement"},
        {"constant": "CAMT_054", "value": "camt.054.001.02", "family": "camt", "description": "Debit/credit notification"},
        {"constant": "PAIN_001", "value": "pain.001.001.09", "family": "pain", "description": "Customer credit transfer initiation"},
    ]
    return message_types

if __name__ == "__main__":
    message_types = get_iso20022_message_types()

    # Test case 1: Check the number of message types
    assert len(message_types) == 5, f"Expected 5 message types, got {len(message_types)}"

    # Test case 2: Check a specific PACS message type's details
    pacs_008 = next((m for m in message_types if m["constant"] == "PACS_008"), None)
    assert pacs_008 is not None, "PACS_008 not found"
    assert pacs_008["value"] == "pacs.008.001.08", f"Expected value 'pacs.008.001.08', got {pacs_008['value']}"
    assert pacs_008["family"] == "pacs", f"Expected family 'pacs', got {pacs_008['family']}"
    assert pacs_008["description"] == "FI to FI customer credit transfer", f"Expected description 'FI to FI customer credit transfer', got {pacs_008['description']}"

    # Test case 3: Check a specific CAMT message type's details and updated version
    camt_053 = next((m for m in message_types if m["constant"] == "CAMT_053"), None)
    assert camt_053 is not None, "CAMT_053 not found"
    assert camt_053["value"] == "camt.053.001.02", f"Expected value 'camt.053.001.02', got {camt_053['value']}"
    assert camt_053["family"] == "camt", f"Expected family 'camt', got {camt_053['family']}"
    assert camt_053["description"] == "Bank to customer statement", f"Expected description 'Bank to customer statement', got {camt_053['description']}"

    # Test case 4: Check a specific PAIN message type's details and updated version
    pain_001 = next((m for m in message_types if m["constant"] == "PAIN_001"), None)
    assert pain_001 is not None, "PAIN_001 not found"
    assert pain_001["value"] == "pain.001.001.09", f"Expected value 'pain.001.001.09', got {pain_001['value']}"
    assert pain_001["family"] == "pain", f"Expected family 'pain', got {pain_001['family']}"

    # Test case 5: Ensure previously listed constants are now absent
    assert next((m for m in message_types if m["constant"] == "PACS_002"), None) is None, "PACS_002 should not be present"
    assert next((m for m in message_types if m["constant"] == "PAIN_002"), None) is None, "PAIN_002 should not be present"


    print("TEST PASSED")
