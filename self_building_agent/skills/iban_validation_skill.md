---
name: iban_validation_skill
tags:
- iban
- validation
- mod97
- financial_data
trigger: when needing to validate an IBAN string using the MOD-97 checksum algorithm
type: pattern
version: 1
success_count: 0
fail_count: 0
---
---
# IBAN Validation Skill
## Purpose
This skill provides a function to validate International Bank Account Numbers (IBANs) using the MOD-97 checksum algorithm. It extracts key components and returns a structured dictionary of the validation results.

## When to use
Use this skill when you need to ensure the integrity and correctness of IBAN strings as part of financial data processing, input validation, or transaction pre-checks.

## How to use
1. Import the `iban_validation_skill` module.
2. Call the `validate_iban(iban_string)` function, passing the IBAN string as an argument.
3. The function will return a dictionary containing:
    - `valid` (bool): True if the IBAN is valid, False otherwise.
    - `country` (str): The two-letter ISO country code if the IBAN is valid or parsed.
    - `check_digits` (str): The two-digit check digits if the IBAN is valid or parsed.
    - `bank_code` (str): The bank code extracted from the IBAN (may vary by country's IBAN structure).
    - `reason` (str): A descriptive string explaining why the IBAN is invalid, or None if valid.
Example:
```python
from iban_validation_skill import validate_iban

iban_to_check = "DE89370400440532013000"
result = validate_iban(iban_to_check)
if result["valid"]:
    print(f"IBAN {iban_to_check} is valid.")
else:
    print(f"IBAN {iban_to_check} is invalid: {result['reason']}")
```