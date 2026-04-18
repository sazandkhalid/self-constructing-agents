---
name: currency_formatter
tags:
- currency
- formatting
- parsing
trigger: when formatting or parsing currency amounts in a payment processing system
type: pattern
version: 1
success_count: 0
fail_count: 0
---
---
# Currency Formatter
## Purpose
Format and parse currency amounts in a payment processing system.
## When to use
Use this skill when displaying or processing currency amounts in a payment processing system.
## How to use
1. Use the format_currency_amount function to format a float amount and a currency code into a human-readable string.
2. Use the parse_currency_amount function to parse a currency string back into a float amount and a currency code.