---
name: generic_validator_skill
tags:
- validation
- generic
- pattern
trigger: when needing to abstract repetitive validation logic into a reusable function
type: pattern
version: 1
success_count: 10
fail_count: 1
---
---
# Generic Validator Skill
## Purpose
This skill provides a generic `validate(obj, rules)` function that allows abstracting validation logic. It accepts an object and a list of callable rules, returning a list of error messages. This promotes code reuse and simplifies the implementation of specific validation functions.
## When to use
Use this skill when you observe a pattern where multiple specific validation functions (e.g., for routing numbers, addresses, account numbers) are implemented by iterating through a set of checks and collecting error messages. This skill can serve as a base for creating more specialized validation functions.
## How to use
1. Import the `validate` function from this skill.
2. Define individual validation rules as separate functions. Each rule function should accept the object being validated and return `None` if the object passes the rule, or a string error message if it fails.
3. Create a list of these rule functions.
4. Call `validate(your_object, your_rule_list)`. The function will return a list of all error messages from the failed rules. An empty list indicates the object is valid.
5. Optionally, create wrapper functions for specific validation needs (e.g., `validate_routing_number(routing_str)`) that define the relevant rules and pass them to the generic `validate` function.