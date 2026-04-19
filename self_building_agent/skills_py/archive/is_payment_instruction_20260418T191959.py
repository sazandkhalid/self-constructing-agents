# skill: is_payment_instruction
# version: 1
# tags: write, function, is_payment_instruction, msg_type, bool
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-18T18:59:34.275663+00:00
# decaying: false
from enum import Enum

class PaymentInstructionType(str, Enum):
    PACS_008 = "pacs.008.001.08"
    PACS_009 = "pacs.009.001.08"
    PAIN_001 = "pain.001.001.08"

def is_payment_instruction(msg_type: str) -> bool:
    'Return True if the message type is a payment instruction.'
    # protocol: iso20022
    # rail: swift_mx
    # audit_required: false
    return msg_type in [payment_type.value for payment_type in PaymentInstructionType]

if __name__ == "__main__":
    assert is_payment_instruction(PaymentInstructionType.PACS_008.value) == True
    assert is_payment_instruction(PaymentInstructionType.PACS_009.value) == True
    assert is_payment_instruction(PaymentInstructionType.PAIN_001.value) == True
    assert is_payment_instruction("camt.053.001.08") == False
    print("TEST PASSED")
