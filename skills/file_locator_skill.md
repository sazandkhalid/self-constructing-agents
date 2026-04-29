---
name: file_locator_skill
tags:
- file
- search
- repository
- utility
trigger: when a file is not found at an expected path within a repository
type: pattern
version: 1
success_count: 0
fail_count: 0
---
---
# File Locator Skill
## Purpose
To search for a file within a specified directory (repository) and return its absolute path if found. This skill is useful when direct file access fails due to incorrect paths or when the exact location of a file is unknown.

## When to use
Use this skill when you encounter a `FileNotFoundError` or a similar error when trying to access a file, and you suspect the file might exist elsewhere in the project's directory structure. It's also useful for general file discovery within a project.

## How to use
1.  **Specify the starting directory:** Provide the root directory of the repository or the directory where the search should begin (e.g., `/Users/sazankhalid/Downloads/self-constructing-agents/self_building_agent/eval/target_repo/fastapi`).
2.  **Specify the filename to search for:** Provide the name of the file you are looking for (e.g., `datastructures.py`).
3.  **Execute the search:** Call the `find_file_in_directory` function with the starting directory and filename.
4.  **Interpret the results:** The function will return the absolute path of the first found file matching the filename, or `None` if the file is not found.