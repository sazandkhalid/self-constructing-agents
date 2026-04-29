# skill: extract_iso20022_messages
# version: 1
# tags: list, message, type, constants, defined
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-27T03:38:01.901507+00:00
# decaying: false
# protocol: general
# rail: general
# audit_required: false
# protocol: general
# rail: general
# audit_required: false
def extract_iso20022_messages(file_path: str) -> dict:
    """
    Extracts ISO 20022 message type constants from a Python file,
    identifying their family and purpose.

    Args:
        file_path: The path to the Python file containing message constants.

    Returns:
        A dictionary where keys are message type constants and values are dictionaries
        containing 'family' and 'purpose'.
    """
    message_data = {}
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return {"error": f"File not found at {file_path}"}
    except Exception as e:
        return {"error": f"An error occurred while reading the file: {e}"}

    # Regex to find constants like:
    # PACS_002_001_09 = "urn:iso:std:iso:20022:tech:xsd:pain.002.001.09"
    # It captures the constant name and the XSD path.
    # We assume the family can be inferred from the constant name or the XSD path.
    pattern = r"([A-Z_0-9]+)\s*=\s*[\"'](urn:iso:std:iso:20022:tech:xsd:([a-z]+)\.([0-9.]+))[\"']"
    matches = re.findall(pattern, content)

    for const_name, full_xsd_path, family_from_xsd, version in matches:
        purpose = ""
        if family_from_xsd == "pacs":
            purpose = "Payment Processing and Cancellation."
        elif family_from_xsd == "camt":
            purpose = "Cash Management and Reporting."
        elif family_from_xsd == "pain":
            purpose = "Payment Initiation."
        else:
            purpose = "Unknown ISO 20022 message family."

        # Fallback to infer family from constant name if not clear from XSD path (less reliable)
        if family_from_xsd not in ["pacs", "camt", "pain"]:
            if "PACS" in const_name:
                family = "pacs"
                purpose = "Payment Processing and Cancellation."
            elif "CAMT" in const_name:
                family = "camt"
                purpose = "Cash Management and Reporting."
            elif "PAIN" in const_name:
                family = "pain"
                purpose = "Payment Initiation."
            else:
                family = "unknown"
                purpose = "Unknown ISO 20022 message family."
        else:
            family = family_from_xsd

        message_data[const_name] = {
            "family": family,
            "purpose": purpose
        }

    return message_data

if __name__ == "__main__":
    import re
    # Create a dummy messages.py file for testing
    dummy_content = """
import re

PACS_002_001_09 = "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.09"
CAMT_053_001_02 = "urn:iso:std:iso:20022:tech:xsd:camt.053.001.02"
PAIN_001_001_03 = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"
UNKNOWN_MSG = "urn:iso:std:iso:20022:tech:xsd:unknown.001.001"
ANOTHER_CAMT = "urn:iso:std:iso:20022:tech:xsd:camt.054.001.01"

# This is a comment and should be ignored
PACS_008_001_08 = "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"
PAIN_002_001_09 = "urn:iso:std:iso:20022:tech:xsd:pain.002.001.09"

# Test case with different formatting
CAMT_052_001_02= "urn:iso:std:iso:20022:tech:xsd:camt.052.001.02"
    """
    with open("messages.py", "w") as f:
        f.write(dummy_content)

    messages = extract_iso20022_messages("messages.py")
    expected_messages = {
        "PACS_002_001_09": {"family": "pacs", "purpose": "Payment Processing and Cancellation."},
        "CAMT_053_001_02": {"family": "camt", "purpose": "Cash Management and Reporting."},
        "PAIN_001_001_03": {"family": "pain", "purpose": "Payment Initiation."},
        "UNKNOWN_MSG": {"family": "unknown", "purpose": "Unknown ISO 20022 message family."},
        "ANOTHER_CAMT": {"family": "camt", "purpose": "Cash Management and Reporting."},
        "PACS_008_001_08": {"family": "pacs", "purpose": "Payment Processing and Cancellation."},
        "PAIN_002_001_09": {"family": "pain", "purpose": "Payment Initiation."},
        "CAMT_052_001_02": {"family": "camt", "purpose": "Cash Management and Reporting."}
    }

    # Basic assertions to check if the extracted data matches expectations
    assert len(messages) == len(expected_messages), f"Expected {len(expected_messages)} messages, but got {len(messages)}"
    for msg, data in expected_messages.items():
        assert msg in messages, f"Message '{msg}' not found in extracted data."
        assert messages[msg] == data, f"Data for '{msg}' mismatch. Expected {data}, got {messages[msg]}"

    # Test file not found
    messages_not_found = extract_iso20022_messages("non_existent_file.py")
    assert "error" in messages_not_found and "File not found" in messages_not_found["error"]

    # Clean up the dummy file
    import os
    os.remove("messages.py")

    print("TEST PASSED")
