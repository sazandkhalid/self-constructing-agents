import os, json, re, yaml, subprocess, tempfile
from datetime import datetime
from collections import deque
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SKILL_CREATION_INSTRUCTIONS = """After completing a task, evaluate whether it warrants a new skill.
Do NOT create a skill that already exists. If a relevant skill is already listed, use it instead.

Only write a skill if ALL of these are true:
- The situation will recur in this specific environment
- The approach was non-obvious and not general programming knowledge
- Something specific to this user/codebase made it different from standard practice

If and ONLY if the task meets all criteria above, use this format:
---NEW SKILL---
filename: skill_name.md
name: skill_name
tags: [tag1, tag2, tag3]
trigger: one sentence describing when this skill should be used
type: pattern
---
# Skill Title
## Purpose
Describe the purpose here.
## When to use
Describe when to use this skill.
## How to use
Describe how to use this skill with concrete steps.
---END SKILL---

Write ACTUAL content. Do NOT use placeholders like [content].
If no skill is needed, just complete the task and stop."""


# ---------------------------------------------------------------------------
# Skill parsing & persistence
# ---------------------------------------------------------------------------

def parse_skill(filepath):
    raw = open(filepath).read()
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        metadata = yaml.safe_load(parts[1]) or {}
        content = parts[2].strip() if len(parts) > 2 else ""
    else:
        metadata = {}
        content = raw

    metadata.setdefault("name", os.path.basename(filepath).replace(".md", ""))
    metadata.setdefault("tags", [])
    metadata.setdefault("trigger", "")
    metadata.setdefault("type", "pattern")
    metadata.setdefault("version", 1)
    metadata.setdefault("success_count", 0)
    metadata.setdefault("fail_count", 0)

    return {"metadata": metadata, "content": content, "filepath": filepath}


def load_all_skills():
    skills = []
    for f in sorted(os.listdir("skills")):
        if f.endswith(".md"):
            skill = parse_skill(f"skills/{f}")
            # Auto-retire: skip skills that consistently fail
            m = skill["metadata"]
            if m["fail_count"] > 5 and m["success_count"] == 0:
                continue
            skills.append(skill)
    return skills


def save_skill(skill):
    frontmatter = yaml.dump(skill["metadata"], default_flow_style=False, sort_keys=False)
    with open(skill["filepath"], "w") as f:
        f.write(f"---\n{frontmatter}---\n{skill['content']}")


# ---------------------------------------------------------------------------
# Skill selection
# ---------------------------------------------------------------------------

def select_skills(task, all_skills):
    if not all_skills:
        return []

    # Stage 1: keyword pre-filter
    task_words = set(re.findall(r'\w+', task.lower()))
    candidates = []
    for s in all_skills:
        m = s["metadata"]
        tag_overlap = len(task_words & set(t.lower() for t in m.get("tags", [])))
        trigger_words = set(re.findall(r'\w+', m.get("trigger", "").lower()))
        trigger_overlap = len(task_words & trigger_words)
        if tag_overlap > 0 or trigger_overlap > 0 or m.get("success_count", 0) > 3:
            candidates.append(s)

    if not candidates:
        return []

    # Stage 2: LLM-based selection
    skill_descriptions = "\n".join(
        f"- {s['metadata']['name']}: {s['metadata'].get('trigger', 'no trigger defined')}"
        for s in candidates
    )
    prompt = f"""Given this task: "{task}"

Which of these skills are relevant? Return ONLY a JSON list of skill names, e.g. ["skill_a"]. If none are relevant, return [].

Available skills:
{skill_descriptions}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip()
        # Extract JSON array from response (LLM may wrap it in text)
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        selected_names = json.loads(match.group()) if match else []
    except Exception:
        selected_names = []

    return [s for s in candidates if s["metadata"]["name"] in selected_names]


# ---------------------------------------------------------------------------
# Code execution
# ---------------------------------------------------------------------------

def extract_code_block(response_text):
    if "---EXECUTE---" not in response_text:
        return None
    block = response_text.split("---EXECUTE---")[1].split("---END EXECUTE---")[0]
    # Strip markdown code fences
    block = re.sub(r'```\w*\n?', '', block).strip()
    return block


def execute_code(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        try:
            result = subprocess.run(
                ['python3', f.name],
                capture_output=True, text=True, timeout=30
            )
            output = result.stdout
            if result.stderr:
                output += "\nSTDERR:\n" + result.stderr
            return output[:2000]
        except subprocess.TimeoutExpired:
            return "ERROR: Execution timed out after 30 seconds"
        finally:
            os.unlink(f.name)


# ---------------------------------------------------------------------------
# Task execution (multi-turn with code execution)
# ---------------------------------------------------------------------------

def run_task(task, selected_skills):
    skill_context = ""
    for s in selected_skills:
        skill_context += f"\n### Skill: {s['metadata']['name']} (type: {s['metadata']['type']})\n{s['content']}\n"

    system = f"""You are a self-building agent. You solve tasks and can execute code.

{"Relevant skills for this task:" + skill_context if skill_context else "No specific skills apply to this task."}

When your response includes code that should be executed, wrap it in:
---EXECUTE---
```python
# code here
```
---END EXECUTE---

When you want to add a follow-up task to the queue, use:
---NEW TASK---
task description here
---END TASK---

{SKILL_CREATION_INSTRUCTIONS}
"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": task}
    ]

    max_iterations = 3
    execution_results = []
    reply = ""

    for i in range(max_iterations):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2000,
            messages=messages
        )
        reply = response.choices[0].message.content

        code = extract_code_block(reply)
        if code:
            result = execute_code(code)
            execution_results.append({"code": code, "result": result})
            print(f"  [Executed code, result: {result[:200]}...]")
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": f"Execution result:\n{result}\n\nContinue or finalize your response."})
        else:
            break

    return reply, execution_results


# ---------------------------------------------------------------------------
# Autonomous task generation
# ---------------------------------------------------------------------------

def extract_new_tasks(response_text):
    tasks = []
    if "---NEW TASK---" not in response_text:
        return tasks
    blocks = response_text.split("---NEW TASK---")[1:]
    for block in blocks:
        task_text = block.split("---END TASK---")[0].strip()
        if task_text and len(task_text) > 5:
            tasks.append(task_text)
    return tasks


# ---------------------------------------------------------------------------
# Skill creation from LLM response
# ---------------------------------------------------------------------------

def extract_and_save_skill(response_text):
    if "---NEW SKILL---" not in response_text:
        return None

    skill_block = response_text.split("---NEW SKILL---")[1]
    skill_block = skill_block.split("---END SKILL---")[0].strip()

    first_line = skill_block.split("\n")[0]
    filename = first_line.replace("filename:", "").strip()
    remaining = "\n".join(skill_block.split("\n")[1:]).strip()

    # Parse frontmatter from the skill block if present
    metadata = {}
    content = remaining
    if remaining.startswith("name:") or remaining.startswith("tags:"):
        # Metadata lines before the markdown content
        meta_lines = []
        body_lines = []
        in_meta = True
        for line in remaining.split("\n"):
            if in_meta and re.match(r'^(name|tags|trigger|type):', line):
                meta_lines.append(line)
            else:
                in_meta = False
                body_lines.append(line)
        if meta_lines:
            try:
                metadata = yaml.safe_load("\n".join(meta_lines)) or {}
            except yaml.YAMLError:
                pass
        content = "\n".join(body_lines).strip()

    # Also handle --- delimited frontmatter
    if remaining.startswith("---"):
        parts = remaining.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                pass
            content = parts[2].strip()

    # Skip placeholder content
    if not content or content.strip("[] \n") in ("content", "content as above", ""):
        print(f"  Skill '{filename}' has placeholder content, skipping.")
        return None

    # Skip duplicates
    existing = {os.path.basename(s["filepath"]) for s in load_all_skills()}
    if filename in existing:
        print(f"  Skill '{filename}' already exists, skipping.")
        return None

    # Build full skill with frontmatter
    metadata.setdefault("name", filename.replace(".md", ""))
    metadata.setdefault("tags", [])
    metadata.setdefault("trigger", "")
    metadata.setdefault("type", "pattern")
    metadata.setdefault("version", 1)
    metadata.setdefault("success_count", 0)
    metadata.setdefault("fail_count", 0)

    skill = {"metadata": metadata, "content": content, "filepath": f"skills/{filename}"}
    save_skill(skill)
    return filename


# ---------------------------------------------------------------------------
# Feedback loop
# ---------------------------------------------------------------------------

def evaluate_skill_usage(task, response, exec_results, selected_skills):
    if not selected_skills:
        return

    skill_names = [s["metadata"]["name"] for s in selected_skills]
    exec_summary = ""
    if exec_results:
        exec_summary = f"\nCode was executed {len(exec_results)} time(s). Last result: {exec_results[-1]['result'][:500]}"

    prompt = f"""Task: "{task}"
Response summary: {response[:500]}
{exec_summary}

Skills used: {skill_names}

For each skill, did it meaningfully help complete this task?
Return ONLY JSON: {{"skill_name": true/false, ...}}"""

    try:
        eval_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = eval_response.choices[0].message.content.strip()
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        verdicts = json.loads(match.group()) if match else {}
    except Exception:
        return

    for skill in selected_skills:
        name = skill["metadata"]["name"]
        if name in verdicts:
            if verdicts[name]:
                skill["metadata"]["success_count"] += 1
                print(f"  Skill '{name}' marked as helpful.")
            else:
                skill["metadata"]["fail_count"] += 1
                print(f"  Skill '{name}' marked as unhelpful.")
            save_skill(skill)

            # Queue a refinement task if skill is consistently failing
            m = skill["metadata"]
            if m["fail_count"] > 3 and m["fail_count"] > m["success_count"]:
                return f"Refine skill '{name}': it has {m['fail_count']} failures vs {m['success_count']} successes. Review and improve or remove it."
    return None


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_result(task, response, skill_written, exec_results=None, new_tasks=None, selected_skills=None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "response": response,
        "skill_written": skill_written,
        "skills_used": [s["metadata"]["name"] for s in (selected_skills or [])],
        "code_executed": len(exec_results) if exec_results else 0,
        "new_tasks_queued": new_tasks or []
    }
    with open("logs/log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    task_queue = deque()

    for line in open("tasks/task_queue.txt").readlines():
        line = line.strip()
        if line:
            task_queue.append(line)

    max_total_tasks = 50
    completed = 0

    while task_queue and completed < max_total_tasks:
        task = task_queue.popleft()
        print(f"\n{'='*60}")
        print(f"Task {completed+1}: {task}")
        print('='*60)

        # 1. Load & select relevant skills
        all_skills = load_all_skills()
        selected = select_skills(task, all_skills)
        if selected:
            print(f"  Skills matched: {[s['metadata']['name'] for s in selected]}")
        else:
            print("  No matching skills found.")

        # 2. Execute task (with possible code execution loop)
        response, exec_results = run_task(task, selected)
        print(response)

        # 3. Extract & save any new skill
        skill = extract_and_save_skill(response)
        if skill:
            print(f"  New skill written: {skill}")

        # 4. Extract & queue any new tasks
        new_tasks = extract_new_tasks(response)
        for nt in new_tasks:
            print(f"  New task queued: {nt}")
            task_queue.append(nt)

        # 5. Evaluate skill usage (feedback loop)
        refinement_task = evaluate_skill_usage(task, response, exec_results, selected)
        if refinement_task:
            print(f"  Refinement task queued: {refinement_task}")
            task_queue.append(refinement_task)

        # 6. Log everything
        log_result(task, response, skill, exec_results, new_tasks, selected)
        completed += 1

    print(f"\nCompleted {completed} tasks.")


if __name__ == "__main__":
    main()
