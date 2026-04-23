---
name: iso20022_message_extractor
tags:
- iso20022
- message extraction
trigger: When extracting ISO 20022 message type constants from a Python file.
type: pattern
version: 1
success_count: 0
fail_count: 1
---
---
# ISO 20022 Message Extractor
## Purpose
Extract ISO 20022 message type constants from a Python file and provide information about their family and purpose.
## When to use
Use this skill when working with ISO 20022 messages and needing to extract message type constants from a Python file.
## How to use
1. Import the necessary modules, including `re` for regular expressions and `os` for file paths.
2. Define a function to extract the message type constants from the Python file.
3. Use regular expressions to find the constants in the file content.
4. Loop through the constants and identify their family (pacs, camt, or pain) and purpose.
5. Return a dictionary or list of the extracted message type constants and their information.