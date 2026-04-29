---
name: message_validator
tags:
- iso20022
- validation
trigger: when needing to validate extracted message type constants
type: pattern
version: 1
success_count: 1
fail_count: 1
---
---
# Message Validator
## Purpose
Validate extracted message type constants against a predefined set of valid constants.
## When to use
Use this skill when working with ISO 20022 messages and needing to validate extracted message type constants.
## How to use
1. Define a set of valid message type constants.
2. Create a function to validate the extracted constants against the valid set.
3. Return a boolean value indicating whether the extracted constants are valid.