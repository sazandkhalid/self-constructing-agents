# skill: validate_iban_and_extract_details
# version: 1
# tags: validate, this, iban, gb82west12345698765432, tell
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-29T22:32:01.246805+00:00
# decaying: false
# protocol: general
# rail: general
# audit_required: false
# protocol: general
# rail: general
# audit_required: false
def validate_iban_and_extract_details(iban: str) -> dict:
    """
    Validates an IBAN (International Bank Account Number) using the MOD-97 checksum algorithm
    and extracts its country code and check digits.

    Args:
        iban: The IBAN string to validate.

    Returns:
        A dictionary containing:
        - 'is_valid': True if the IBAN is valid, False otherwise.
        - 'country': The country code (first two uppercase letters).
        - 'check_digits': The check digits (third and fourth digits).
        - 'error': An error message if validation fails for structural reasons, None otherwise.
    """
    import re

    if not isinstance(iban, str):
        return {"is_valid": False, "country": None, "check_digits": None, "error": "Input must be a string."}

    original_iban = iban
    iban = iban.replace(" ", "").upper()

    # Basic structure check
    if not re.fullmatch("[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", iban):
        return {"is_valid": False, "country": iban[:2] if len(iban) >=2 else None, "check_digits": iban[2:4] if len(iban) >=4 else None, "error": "IBAN does not match basic structural pattern."}

    # Extract country and check digits before rearrangement for MOD-97
    country_code = iban[:2]
    check_digits = iban[2:4]

    # Move the first four characters to the end for MOD-97 calculation
    rearranged_iban = iban[4:] + iban[:4]

    # Replace letters with numbers (A=10, B=11, ..., Z=35)
    numeric_iban_parts = []
    for char in rearranged_iban:
        if 'A' <= char <= 'Z':
            numeric_iban_parts.append(str(ord(char) - ord('A') + 10))
        else:
            numeric_iban_parts.append(char)
    numeric_iban = "".join(numeric_iban_parts)

    # Calculate the MOD-97 checksum
    try:
        is_valid = int(numeric_iban) % 97 == 1
    except ValueError:
        is_valid = False
        error_msg = "Could not convert IBAN to a numeric string for checksum calculation."
    except Exception as e:
        is_valid = False
        error_msg = f"An unexpected error occurred during checksum calculation: {e}"
    else:
        error_msg = None

    return {
        "is_valid": is_valid,
        "country": country_code,
        "check_digits": check_digits,
        "error": error_msg
    }

if __name__ == "__main__":
    # Test cases
    valid_iban = "GB82WEST12345698765432"
    result_valid = validate_iban_and_extract_details(valid_iban)
    assert result_valid["is_valid"] is True, f"Valid IBAN failed: {result_valid}"
    assert result_valid["country"] == "GB", f"Valid IBAN country incorrect: {result_valid['country']}"
    assert result_valid["check_digits"] == "82", f"Valid IBAN check digits incorrect: {result_valid['check_digits']}"
    assert result_valid["error"] is None, f"Valid IBAN reported error: {result_valid['error']}"

    invalid_checksum_iban = "GB83WEST12345698765432" # Changed check digits from 82 to 83
    result_invalid_checksum = validate_iban_and_extract_details(invalid_checksum_iban)
    assert result_invalid_checksum["is_valid"] is False, f"Invalid checksum IBAN passed: {result_invalid_checksum}"
    assert result_invalid_checksum["country"] == "GB", f"Invalid checksum IBAN country incorrect: {result_invalid_checksum['country']}"
    assert result_invalid_checksum["check_digits"] == "83", f"Invalid checksum IBAN check digits incorrect: {result_invalid_checksum['check_digits']}"
    assert result_invalid_checksum["error"] is None, f"Invalid checksum IBAN reported error: {result_invalid_checksum['error']}"


    invalid_format_iban = "GB22WEST12345" # Too short
    result_invalid_format = validate_iban_and_extract_details(invalid_format_iban)
    assert result_invalid_format["is_valid"] is False, f"Invalid format IBAN (short) passed: {result_invalid_format}"
    assert result_invalid_format["error"] is not None, f"Invalid format IBAN (short) did not report error: {result_invalid_format['error']}"

    invalid_chars_iban = "DE12A-B3456789012345678" # Contains hyphen
    result_invalid_chars = validate_iban_and_extract_details(invalid_chars_iban)
    assert result_invalid_chars["is_valid"] is False, f"Invalid format IBAN (chars) passed: {result_invalid_chars}"
    assert result_invalid_chars["error"] is not None, f"Invalid format IBAN (chars) did not report error: {result_invalid_chars['error']}"

    empty_iban = ""
    result_empty = validate_iban_and_extract_details(empty_iban)
    assert result_empty["is_valid"] is False, f"Empty IBAN passed: {result_empty}"
    assert result_empty["error"] is not None, f"Empty IBAN did not report error: {result_empty['error']}"

    non_string_iban = 12345
    result_non_string = validate_iban_and_extract_details(non_string_iban)
    assert result_non_string["is_valid"] is False, f"Non-string IBAN passed: {result_non_string}"
    assert result_non_string["error"] is not None, f"Non-string IBAN did not report error: {result_non_string['error']}"

    print("TEST PASSED")
