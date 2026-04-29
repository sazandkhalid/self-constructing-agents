# skill: get_public_class_names_in_dir
# version: 1
# tags: locate, every, python, file, under
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T22:53:18.260360+00:00
# decaying: false
import os
import ast

def get_public_class_names_in_dir(directory_path):
    """
    Finds all Python files in a directory and reports the public class names defined in each.

    Args:
        directory_path (str): The path to the directory to scan.

    Returns:
        dict: A dictionary where keys are relative file paths and values are lists of public class names.
    """
    public_classes_by_file = {}

    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                relative_file_path = os.path.relpath(file_path, directory_path)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                    
                    public_classes = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            if not node.name.startswith("_"):
                                public_classes.append(node.name)
                    
                    if public_classes:
                        public_classes_by_file[relative_file_path] = public_classes
                except Exception as e:
                    print(f"Could not parse file {file_path}: {e}")
    
    return public_classes_by_file

if __name__ == "__main__":
    # Assume the repository root is the current working directory for this example
    # In a real execution, you might need to adjust this path based on where the script is run
    # For this example, we'll simulate the structure
    
    # Create dummy directory and files for testing
    if not os.path.exists("fastapi/security"):
        os.makedirs("fastapi/security")
    
    with open("fastapi/security/auth.py", "w") as f:
        f.write("class PublicAuth:\n    pass\n\nclass _PrivateAuth:\n    pass\n")
    with open("fastapi/security/oauth2.py", "w") as f:
        f.write("class OAuth2PasswordBearer:\n    pass\n\nclass TokenData:\n    pass\n")
    with open("fastapi/security/api_key.py", "w") as f:
        f.write("class APIKey:\n    pass\n\nclass _APIKeyBase:\n    pass\n")
    with open("fastapi/security/__init__.py", "w") as f: # Empty file, should not appear in output
        pass

    
    # The actual directory to scan, relative to where this script would run within the repo
    # For the purpose of this test, it's 'fastapi/security'
    test_dir = "fastapi/security"
    result = get_public_class_names_in_dir(test_dir)
    
    expected_result = {
        "auth.py": ["PublicAuth"],
        "oauth2.py": ["OAuth2PasswordBearer", "TokenData"],
        "api_key.py": ["APIKey"]
    }
    
    # Sort lists for consistent comparison
    for k in result:
        result[k].sort()
    for k in expected_result:
        expected_result[k].sort()

    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Clean up dummy files and directories
    import shutil
    shutil.rmtree("fastapi")

    print("TEST PASSED")
