---
name: param_subclass_skill
tags:
- fastapi
- param
- subclass
trigger: when creating custom Param subclasses in FastAPI applications
type: pattern
version: 1
success_count: 0
fail_count: 1
---
---
# Param Subclass Skill
## Purpose
Create `Param` subclasses following the same metaclass-free pattern as used in `fastapi/params.py`, allowing for customization of parameter validation and parsing.

## When to use
Use this skill when creating custom `Param` subclasses in FastAPI applications, particularly when working with `fastapi/params.py` and related modules.

## How to use
1. Import the `Param` class from `fastapi/params.py`.
2. Define a new class that inherits from `Param`.
3. Implement the required methods, such as `__init__` and `validate`, to customize parameter validation and parsing.
4. Use the custom `Param` subclass in your FastAPI application to handle parameter validation and parsing.