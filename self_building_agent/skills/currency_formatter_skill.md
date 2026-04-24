---
name: currency_formatter_skill
tags:
- currency
- formatting
- display
trigger: when needing to format currency amounts for display or logging purposes
type: pattern
version: 1
success_count: 0
fail_count: 1
---
---
# Currency Formatter Skill
## Purpose
This skill provides a standardized way to format currency amounts into human-readable strings, including currency symbols or codes, and to parse them back into numerical values.
## When to use
Use this skill when you need to display currency values to users, log financial data, or convert user-input currency strings back into a format suitable for processing. This is particularly useful for ensuring consistency in how financial data is presented across different parts of an application.
## How to use
1.  **Formatting an amount:** Call the `format_currency_amount` function with the amount (float or Decimal) and the ISO currency code (e.g., "EUR", "USD"). The function will return a formatted string (e.g., "€1,234.56" or "USD 1,234.56").
2.  **Parsing an amount:** Call the `parse_currency_amount` function with a formatted currency string. The function will attempt to return a tuple containing the numeric amount (float) and the currency code.