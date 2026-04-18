---
name: iso20022_parser
tags:
- iso20022
- parsing
- camt053
trigger: when parsing or processing ISO 20022 messages
type: pattern
version: 1
success_count: 4
fail_count: 3
---
---
# ISO 20022 Parser
## Purpose
Parse and process ISO 20022 messages, including camt.053 bank statements.
## When to use
Use this skill when parsing or processing ISO 20022 messages, such as extracting entries from a camt.053 bank statement.
## How to use
1. Import the necessary modules, including `xml.etree.ElementTree` and `dataclasses`.
2. Define a dataclass to represent the extracted entries, such as `Entry`.
3. Use the `extract_entries` function to extract entries from a camt.053 bank statement XML string.
4. Validate the extracted entries against a predefined schema or rules.