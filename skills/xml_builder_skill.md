---
name: xml_builder_skill
tags:
- xml
- generation
- builder
trigger: when needing to generate simple XML elements with optional attributes
type: pattern
version: 1
success_count: 2
fail_count: 0
---
---
# XML Builder Skill
## Purpose
This skill provides a function to generate simple XML element strings, supporting the inclusion of attributes. It's designed for creating basic XML structures without the complexity of a full XML parser/builder.
## When to use
Use this skill when you need to programmatically construct XML strings for data formats, configuration files, or simple API responses where the XML structure is predictable and not deeply nested.
## How to use
1. Import the `build_xml_element` function.
2. Call the function with the tag name, the element's value, and an optional dictionary of attributes.
   ```python
   from your_skill_library import build_xml_element

   # Create an element without attributes
   element1 = build_xml_element("Message", "Hello, World!")
   # element1 will be "<Message>Hello, World!</Message>"

   # Create an element with attributes
   element2 = build_xml_element("Amount", "100.50", {"currency": "USD", "type": "debit"})
   # element2 might be '<Amount currency="USD" type="debit">100.50</Amount>' (order of attributes may vary)
   ```