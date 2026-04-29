# skill: list_all_skills_in_directory
# version: 1
# tags: list, skills, directory
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-29T19:49:49.856255+00:00
# decaying: false
# protocol: general
# rail: general
# audit_required: false
# protocol: general
# rail: general
# audit_required: false
import json
import os

def list_all_skills_in_directory():
    """
    Lists all skills by reading the skills_py/index.json file.
    """
    try:
        current_dir = os.path.dirname(__file__)
        index_path = os.path.join(current_dir, 'index.json')
        
        # Fallback for when executed from a different directory (e.g., agent root)
        if not os.path.exists(index_path):
            index_path = 'skills_py/index.json'

        with open(index_path, 'r') as f:
            skills_data = json.load(f)

        skill_names = [skill_name for skill_name in skills_data.keys()]
        return skill_names
    except FileNotFoundError:
        return ["Error: skills_py/index.json not found."]
    except json.JSONDecodeError:
        return ["Error: Could not decode skills_py/index.json. Is it valid JSON?"]
    except Exception as e:
        return [f"An unexpected error occurred: {e}"]

if __name__ == "__main__":
    # To test this, you'd typically have an index.json in the skills_py directory
    # For a self-contained test, we'll create a dummy one if it doesn't exist.
    # In a real scenario, this would be part of the agent's environment setup.

    dummy_index_content = {
        "skill_a": {"description": "Skill A"},
        "skill_b": {"description": "Skill B"},
        "get_iso20022_message_types": {"description": "Gets ISO 20022 message types"}
    }
    
    # Ensure skills_py directory exists for testing purposes
    if not os.path.exists('skills_py'):
        os.makedirs('skills_py')
        
    dummy_index_path = 'skills_py/index.json'
    original_content = None

    try:
        if os.path.exists(dummy_index_path):
            with open(dummy_index_path, 'r') as f:
                original_content = f.read()
        
        with open(dummy_index_path, 'w') as f:
            json.dump(dummy_index_content, f)

        skills = list_all_skills_in_directory()
        print(f"Discovered skills: {skills}")
        expected_skills = sorted(["skill_a", "skill_b", "get_iso20022_message_types"])
        assert sorted(skills) == expected_skills, f"Expected {expected_skills}, got {skills}"
        print("TEST PASSED")

    finally:
        # Clean up the dummy file
        if os.path.exists(dummy_index_path):
            if original_content:
                with open(dummy_index_path, 'w') as f:
                    f.write(original_content)
            else:
                os.remove(dummy_index_path)
