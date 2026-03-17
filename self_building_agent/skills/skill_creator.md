---
name: skill_creator
tags: [skill, evaluation, meta, agent]
trigger: task involves deciding whether to create a new reusable skill
type: checklist
version: 1
success_count: 0
fail_count: 0
---
# Skill: Skill Evaluation

## Purpose
Decide whether a completed task warrants writing a new skill.

## When to evaluate
After every task, before deciding to write a skill.

## Questions to ask
1. Would I encounter this situation again in this environment?
2. Did I have to figure out something non-obvious that isn't general knowledge?
3. Is there something specific to this user/codebase/domain that made this task different?
4. Would a skill here meaningfully help future performance, or is this just a standard task?

## Decision rule
Only write a skill if you answer YES to at least 2 of the 4 questions above.

## What does NOT need a skill
- Standard programming patterns (sorting, string manipulation, basic algorithms)
- Tasks that were completed correctly on the first try with no uncertainty
- One-off tasks that are unlikely to recur
- Anything covered well by general knowledge

## What DOES need a skill
- Project-specific conventions discovered during the task
- API quirks or non-standard tool behaviors encountered
- Error patterns that required non-obvious recovery
- Domain-specific approaches that differ from general best practice
- Tasks where the first approach failed and a better one was found
