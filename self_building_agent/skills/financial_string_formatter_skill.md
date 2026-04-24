---
name: financial_string_formatter_skill
tags:
- financial
- formatting
- IBAN
- currency
trigger: when needing to format or validate financial strings like IBANs, account
  numbers, etc.
type: pattern
version: 1
success_count: 2
fail_count: 6
---
---
# Financial String Formatter Skill
## Purpose
This skill provides functions for formatting and validating common financial string formats, such as IBANs, account numbers, and routing numbers.

## When to use
Use this skill when you need to standardize or validate financial identifiers to ensure consistency and correctness in financial data processing.

## How to use
1. Import the `financial_string_formatter_skill` module.
2. Call the relevant function, e.g., `format_iban(iban_string)` to clean and standardize an IBAN.
3. For validation, use functions like `is_valid_iban(iban_string)`.