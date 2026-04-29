---
name: iso20022_parser_registry
tags:
- iso20022
- parser
- registry
- dynamic loading
trigger: when needing to implement a flexible and extensible ISO 20022 message parsing
  system without hardcoding parser dispatch logic.
type: pattern
version: 1
success_count: 1
fail_count: 0
---
---
# ISO 20022 Parser Registry Pattern
## Purpose
To create a dynamic and extensible system for parsing various ISO 20022 message types. Instead of hardcoding a large `if/elif` chain for message type dispatch, this pattern uses a registry to map message type identifiers to their corresponding parsing functions. This allows for easier addition of new message types and parsers without modifying the core dispatch logic.

## When to use
When dealing with a growing number of ISO 20022 message types that require distinct parsing logic. This is particularly useful in systems that need to process a wide range of ISO 20022 messages (e.g., pacs, camt, pain families) and where maintainability and extensibility are key.

## How to use
1.  **Define Parser Interface:** Ensure all individual parser functions (e.g., `parse_pacs008`, `extract_statement_entries`) adhere to a consistent signature, accepting an XML string and returning a structured output (e.g., a dictionary or dataclass instance).
2.  **Create a Registry:** Implement a dictionary or a similar data structure that maps ISO 20022 message type strings (e.g., `"pacs.008.001.08"`) to their corresponding parsing functions.
3.  **Implement Dispatcher Function:** Create a central function (e.g., `parse_iso20022_message`) that takes the `xml_string` and `msg_type` as input. This function will:
    *   Look up the `msg_type` in the registry.
    *   If found, call the associated parsing function with the `xml_string`.
    *   If not found, handle the unknown message type appropriately (e.g., return an error).
    *   Optionally, determine the message family (pacs, camt, pain) based on the `msg_type`.
    *   Normalize the output into a consistent format, including the original `msg_type`, determined `family`, the parsed `payload`, and any `parse_error`.
4.  **Dynamic Loading (Optional but Recommended):** For advanced extensibility, consider a mechanism to automatically discover and register parsers from specific modules or directories at application startup. This could involve Python's importlib or a simple file-scanning approach.
5.  **Error Handling:** Implement robust error handling for cases where parsing fails, the message type is unknown, or the XML is malformed.