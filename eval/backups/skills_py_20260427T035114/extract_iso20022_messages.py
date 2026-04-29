# skill: extract_iso20022_messages
# version: 1
# tags: list, message, type, constants, defined
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-27T03:48:56.780232+00:00
# decaying: false
import re

# protocol: general
# rail: general
# audit_required: false
def extract_iso20022_messages(file_content):
    """
    Extracts ISO 20022 message type constants, their families, and purposes from file content.
    """
    messages = {}
    # Regex to find constants like PACS_008 = "pacs.008.001.08"   # FI to FI customer credit transfer
    # It captures the constant name, the message type string, and the comment description.
    pattern = re.compile(r"(\w+)\s*=\s*\"(.*?)\"(?:\s*#\s*(.*))?")
    
    for match in pattern.finditer(file_content):
        constant_name, message_type, description = match.groups()
        
        family = "unknown"
        if constant_name.startswith("PACS_"):
            family = "pacs"
        elif constant_name.startswith("CAMT_"):
            family = "camt"
        elif constant_name.startswith("PAIN_"):
            family = "pain"
            
        messages[constant_name] = {
            "message_type": message_type,
            "family": family,
            "description": description.strip() if description else ""
        }
    return messages

if __name__ == "__main__":
    # Mock file content based on the provided snippet
    mock_file_content = """
ISO 20022 message type registry.
Covers pacs (payments clearing), camt (cash management), pain (payment initiation).
"""
    # Add a more realistic example of constants as seen in real ISO 20022 definitions
    mock_file_content += """
PACS_008 = "pacs.008.001.08"   # FI to FI customer credit transfer
PACS_009 = "pacs.009.001.08"   # FI credit transfer
CAMT_053 = "camt.053.001.02"   # Bank to customer statement
CAMT_054 = "camt.054.001.02"   # Debit/credit notification
PAIN_001 = "pain.001.001.09"   # Customer credit transfer initiation
PAIN_002 = "pain.002.001.09"   # Customer payment status report
"""

    messages_info = extract_iso20022_messages(mock_file_content)
    
    # Assertions based on the mock content
    assert "PACS_008" in messages_info
    assert messages_info["PACS_008"]["family"] == "pacs"
    assert messages_info["PACS_008"]["description"] == "FI to FI customer credit transfer"
    
    assert "PACS_009" in messages_info
    assert messages_info["PACS_009"]["family"] == "pacs"
    assert messages_info["PACS_009"]["description"] == "FI credit transfer"

    assert "CAMT_053" in messages_info
    assert messages_info["CAMT_053"]["family"] == "camt"
    assert messages_info["CAMT_053"]["description"] == "Bank to customer statement"

    assert "CAMT_054" in messages_info
    assert messages_info["CAMT_054"]["family"] == "camt"
    assert messages_info["CAMT_054"]["description"] == "Debit/credit notification"

    assert "PAIN_001" in messages_info
    assert messages_info["PAIN_001"]["family"] == "pain"
    assert messages_info["PAIN_001"]["description"] == "Customer credit transfer initiation"

    assert "PAIN_002" in messages_info
    assert messages_info["PAIN_002"]["family"] == "pain"
    assert messages_info["PAIN_002"]["description"] == "Customer payment status report"
    
    print("TEST PASSED")
