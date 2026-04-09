---
name: resolve_class_name_conflicts
tags:
- class_name_conflicts
- multiple_classes
- context_resolution
trigger: when multiple classes with the same name are found in different files
type: pattern
version: 1
success_count: 1
fail_count: 4
---
---
# Resolve Class Name Conflicts
## Purpose
Resolve class name conflicts when multiple classes with the same name are found in different files, based on additional context or configuration.

## When to use
Use this skill when multiple classes with the same name are found in different files, and the correct class needs to be resolved based on additional context or configuration.

## How to use
1. Define the context or configuration that will be used to resolve the class name conflict.
2. Traverse the files and extract information about the classes with the conflicting name.
3. Use the context or configuration to determine the correct class.
4. Return the correct class and its corresponding file path.