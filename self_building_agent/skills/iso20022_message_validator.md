---
name: iso20022_message_validator
tags:
- iso20022
- message validation
trigger: when validating message types against a predefined schema or rules
type: pattern
version: 1
success_count: 0
fail_count: 0
---
---
# ISO 20022 Message Validator
## Purpose
Validate message types against a predefined schema or rules to ensure they are well-formed and conform to the ISO 20022 standard.

## When to use
Use this skill when validating message types against a predefined schema or rules, such as when parsing or processing ISO 20022 messages.

## How to use
1. Import the necessary modules, including `xml.etree.ElementTree` and `dataclasses`.
2. Define a dataclass to represent the message type and its schema.
3. Use the `validate_message_type` function to validate the message type against the schema.
4. Return a boolean indicating whether the message type is valid.