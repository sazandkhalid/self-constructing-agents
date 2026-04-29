# skill: get_public_class_names
# version: 1
# tags: locate, every, python, file, under
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T22:53:00.970526+00:00
# decaying: false
import os
import ast

def get_public_class_names(directory_path):
    """
    Finds all Python files in a directory and reports the public class names defined in each.

    Args:
        directory_path (str): The path to the directory to scan.

    Returns:
        dict: A dictionary where keys are file paths and values are lists of public class names.
    """
    public_classes_by_file = {}

    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                        public_classes = []
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                # Check if the class name is "public" (does not start with '_')
                                if not node.name.startswith("_"):
                                    public_classes.append(node.name)
                        if public_classes:
                            public_classes_by_file[file_path] = public_classes
                except FileNotFoundError:
                    print(f"Error: File not found at {file_path}")
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
    return public_classes_by_file

# Unit tests
if __name__ == "__main__":
    # Create a dummy directory structure and files for testing
    test_dir = "temp_fastapi_security_test"
    os.makedirs(os.path.join(test_dir, "subdir"), exist_ok=True)

    with open(os.path.join(test_dir, "file1.py"), "w") as f:
        f.write("""
class PublicClass1:
    pass

class _PrivateClass1:
    pass
""")

    with open(os.path.join(test_dir, "file2.py"), "w") as f:
        f.write("""
class PublicClass2:
    def __init__(self):
        pass

class AnotherPublicClass:
    pass

class _AnotherPrivateClass:
    pass
""")

    with open(os.path.join(test_dir, "subdir", "file3.py"), "w") as f:
        f.write("""
class SubdirPublicClass:
    pass
""")

    with open(os.path.join(test_dir, "empty_file.py"), "w") as f:
        f.write("")

    result = get_public_class_names(test_dir)
    expected_result = {
        os.path.join(test_dir, "file1.py"): ["PublicClass1"],
        os.path.join(test_dir, "file2.py"): ["PublicClass2", "AnotherPublicClass"],
        os.path.join(test_dir, "subdir", "file3.py"): ["SubdirPublicClass"]
    }

    # Sort lists for reliable comparison
    for k in result:
        result[k].sort()
    for k in expected_result:
        expected_result[k].sort()

    assert result == expected_result, f"Test Failed: Expected {expected_result}, got {result}"

    # Clean up dummy files and directory
    os.remove(os.path.join(test_dir, "file1.py"))
    os.remove(os.path.join(test_dir, "file2.py"))
    os.remove(os.path.join(test_dir, "subdir", "file3.py"))
    os.remove(os.path.join(test_dir, "empty_file.py"))
    os.rmdir(os.path.join(test_dir, "subdir"))
    os.rmdir(test_dir)

    print("TEST PASSED")
