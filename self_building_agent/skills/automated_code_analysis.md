---
name: automated_code_analysis
tags: [python, linting, complexity, analysis, monitoring, watchdog]
trigger: task involves analyzing Python code quality, linting, or complexity scoring
type: tool
version: 1
success_count: 0
fail_count: 0
---
# Automated Code Analysis
## Purpose
Automatically monitor a folder for new Python files, run them through a linter and complexity scorer, and generate a summary using a Large Language Model.

## When to use
Use this skill when you need to automate the analysis of new Python code in a specified directory, including linting, complexity scoring, and summary generation.

## How to use
1. **Install Required Libraries**: Run `pip install watchdog pylint mccabe transformers sentence-transformers torch` to ensure you have all necessary libraries.
2. **Create the Monitoring Script**: Create a Python script similar to `monitor_folder.py` provided above.
3. **Specify the Directory to Monitor**: Modify the `path` parameter in `observer.schedule` to the directory you want to monitor.
4. **Run the Monitoring Script**: Execute the Python script to start monitoring the directory.
5. **Analyze New Files**: Upon detection of a new Python file, the script will automatically run linting and complexity analysis.
