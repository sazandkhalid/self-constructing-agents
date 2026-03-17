---
name: prompt_versioning
tags: [prompts, versioning, rollback, templates, llm]
trigger: task involves managing, versioning, or rolling back LLM prompt templates
type: pattern
version: 1
success_count: 0
fail_count: 0
---
# Prompt Versioning System
## Purpose
Manage prompt templates for LLM calls with version tracking, rollback capabilities, and efficient reuse.

## When to use
Use this skill when you need to manage multiple versions of prompt templates, track which version was used for each call, and revert to a previous version if needed.

## How to use
1. Create a `prompt_templates/versions/` folder for versioned templates.
2. Save each version as `prompt_v1.txt`, `prompt_v2.txt`, etc.
3. Log each LLM call with the prompt version used.
4. Rollback by switching to a previous version file.

### Implementation Example
```python
import csv, os
from datetime import datetime

VERSIONS_FOLDER = 'prompt_templates/versions'
LOG_FILE = 'prompt_templates/llm_call_log.csv'

def log_llm_call(prompt_version, input_prompt, response):
    with open(LOG_FILE, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'prompt_version', 'input_prompt', 'response'])
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow({'timestamp': datetime.now().isoformat(), 'prompt_version': prompt_version, 'input_prompt': input_prompt, 'response': response})

def load_prompt_template(version):
    path = os.path.join(VERSIONS_FOLDER, f'prompt_v{version}.txt')
    return open(path).read() if os.path.exists(path) else None
```
