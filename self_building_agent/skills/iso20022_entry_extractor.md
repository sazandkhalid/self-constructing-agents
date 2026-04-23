---
name: iso20022_entry_extractor
tags:
- iso20022
- camt.053
- entry extraction
trigger: when extracting entries from a camt.053 bank statement
type: pattern
version: 1
success_count: 1
fail_count: 0
---
---
# ISO 20022 Entry Extractor
## Purpose
Extract structured fields from a camt.053 bank statement.
## When to use
Use this skill when parsing a camt.053 bank statement and extracting entries.
## How to use
1. Read the camt.053 bank statement XML string.
2. Use the `extract_entries` function to extract entries from the XML string.
3. Validate the extracted entries against a predefined schema or rules.