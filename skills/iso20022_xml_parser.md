---
name: iso20022_xml_parser
tags:
- iso20022
- xml
- parser
trigger: when parsing ISO 20022 XML messages
type: pattern
version: 1
success_count: 3
fail_count: 0
---
---
# ISO 20022 XML Parser
## Purpose
Extract structured fields from ISO 20022 XML messages.
## When to use
Use this skill when parsing ISO 20022 XML messages, such as camt.053 bank statements.
## How to use
1. Import the necessary libraries, including xml.etree.ElementTree.
2. Define a function to extract entries from the XML string, using ElementTree to parse the XML.
3. Use the function to extract entries from the XML string.