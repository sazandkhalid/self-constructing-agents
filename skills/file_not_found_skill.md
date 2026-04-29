---
name: file_not_found_skill
tags:
- file_not_found
- error_handling
trigger: when encountering a FileNotFoundError while trying to open a file
type: pattern
version: 1
success_count: 0
fail_count: 0
---
---
# File Not Found Skill
## Purpose
Handle FileNotFoundError exceptions when trying to open a file.
## When to use
Use this skill when a file is not found in the expected location.
## How to use
1. Check if the file exists before trying to open it.
2. If the file does not exist, handle the error accordingly (e.g., print an error message, return a default value, etc.).