---
name: xml_field_extractor_skill
tags:
- xml
- parsing
- extraction
- regex
trigger: when needing to extract a specific field's value from a simple XML string
  using regex
type: pattern
version: 1
success_count: 4
fail_count: 0
---
---
# XML Field Extractor Skill
## Purpose
This skill provides a function to extract the value of a specific tag from a simple XML string using regular expressions. It is designed for straightforward XML structures where tags do not contain complex attributes or nested structures that would require a full XML parser.
## When to use
Use this skill when you need to quickly extract a single, known tag's content from an XML string and the string is not overly complex (e.g., no CDATA sections, self-closing tags with content, or deeply nested elements that might be confused by a simple regex).
## How to use
1. Import the `extract_xml_field` function.
2. Call the function with the XML string and the target tag name.
   ```python
   from your_skill_library import extract_xml_field

   xml_data = "<MsgId>12345</MsgId><Amount>100.50</Amount>"
   message_id = extract_xml_field(xml_data, "MsgId")
   # message_id will be "12345"
   missing_field = extract_xml_field(xml_data, "Reference")
   # missing_field will be ""
   ```