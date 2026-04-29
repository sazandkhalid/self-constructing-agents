# skill: iban_validation_skill
# version: 1
# tags: validate, this, iban, gb82west12345698765432
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-29T20:17:35.439137+00:00
# decaying: false
# protocol: general
# rail: general
# audit_required: false
# protocol: general
# rail: general
# audit_required: false
def iban_validation_skill(iban: str) -> bool:
    """
    Validates an IBAN (International Bank Account Number) using the MOD-97 checksum algorithm.

    The validation process involves:
    1. Moving the four initial characters to the end of the string.
    2. Replacing each letter with two digits, where A=10, B=11, ..., Z=35.
    3. Interpreting the resulting string as a decimal integer and computing the remainder
       when divided by 97.
    4. If the remainder is 1, the IBAN is valid.

    Args:
        iban: The IBAN string to validate.

    Returns:
        True if the IBAN is valid, False otherwise.
    """
    if not isinstance(iban, str):
        return False
    
    iban = iban.replace(" ", "").upper()

    if len(iban) < 15 or len(iban) > 34:  # IBANs are typically 15-34 characters long
        return False

    # Move the four initial characters to the end of the string
    rearranged_iban = iban[4:] + iban[:4]

    # Replace each letter with two digits (A=10, B=11, ..., Z=35)
    numeric_iban_parts = []
    for char in rearranged_iban:
        if 'A' <= char <= 'Z':
            numeric_iban_parts.append(str(ord(char) - ord('A') + 10))
        elif '0' <= char <= '9':
            numeric_iban_parts.append(char)
        else:
            return False  # Invalid character

    numeric_iban = "".join(numeric_iban_parts)

    # Compute the remainder when divided by 97
    try:
        # Process in chunks to avoid excessively large integer conversion
        # This is a common technique for large number modulo operations
        remainder = 0
        for digit in numeric_iban:
            remainder = (remainder * 10 + int(digit)) % 97
        return remainder == 1
    except ValueError:
        return False # Should not happen if previous checks are correct
    except Exception:
        return False # Catch any other unexpected errors


if __name__ == "__main__":
    # Test cases for iban_validation_skill
    assert iban_validation_skill("GB82WEST12345698765432") == True, "Test Case 1 Failed: Valid IBAN"
    assert iban_validation_skill("GB82WEST12345698765433") == False, "Test Case 2 Failed: Invalid Checksum"
    assert iban_validation_skill("NL91ABNA0417164300") == True, "Test Case 3 Failed: Valid NL IBAN"
    assert iban_validation_skill("DE89370400440532013000") == True, "Test Case 4 Failed: Valid DE IBAN"
    assert iban_validation_skill("FR1420041010050500013M02606") == True, "Test Case 5 Failed: Valid FR IBAN"
    assert iban_validation_skill("GB82WEST12345698765432A") == False, "Test Case 6 Failed: Too long"
    assert iban_validation_skill("GB82WEST1234569876543") == False, "Test Case 7 Failed: Too short"
    assert iban_validation_skill("GB82WEST1234569876543_") == False, "Test Case 8 Failed: Invalid character"
    assert iban_validation_skill("") == False, "Test Case 9 Failed: Empty string"
    assert iban_validation_skill(123) == False, "Test Case 10 Failed: Non-string input"
    assert iban_validation_skill("GB82 WEST 1234 5698 7654 32") == True, "Test Case 11 Failed: IBAN with spaces"

    print("TEST PASSED")
