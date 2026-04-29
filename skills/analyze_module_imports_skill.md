---
name: analyze_module_imports_skill
tags:
- code-analysis
- imports
- python
- repository
trigger: when needing to identify and report on how a specific Python module is imported
  across multiple files in a repository.
type: pattern
version: 1
success_count: 2
fail_count: 0
---
---
# Analyze Module Imports Skill
## Purpose
To identify and report on the import patterns of a specific Python module across all Python files within a given repository directory. This skill helps in understanding dependencies and potential areas for refactoring or optimization.
## When to use
Use this skill when you need to:
- Understand how a particular library (e.g., `starlette`, `pydantic`, `sqlalchemy`) is used across a codebase.
- Identify all files that depend on a specific module.
- Prepare for refactoring or upgrading a library by understanding its usage.
- Audit dependencies within a project.
## How to use
1. **Specify the target module:** Determine the name of the Python module you want to analyze (e.g., `starlette`, `pydantic`).
2. **Specify the repository path:** Provide the absolute or relative path to the root directory of the repository you are analyzing.
3. **Execute the skill:** Run the `analyze_module_imports` function with the module name and repository path as arguments.
4. **Review the output:** The skill will return a dictionary where keys are file paths containing imports of the specified module, and values are lists of the imported names (or `*` if the whole module was imported).

Example usage:
```python
# Assuming this skill is saved as analyze_module_imports_skill.py
from analyze_module_imports_skill import analyze_module_imports

repo_path = "/path/to/your/repository"
module_name = "starlette"
imports_info = analyze_module_imports(repo_path, module_name)

for file_path, imported_names in imports_info.items():
    print(f"File: {file_path}")
    print(f"  Imports: {', '.join(imported_names)}")
```