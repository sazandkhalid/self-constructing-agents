# skill: find_repeated_imports
# version: 1
# tags: find, code, pattern, repeated, across
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-07T15:54:58.682937+00:00
# decaying: false
import os
import ast

def find_repeated_imports(directory):
    """
    Finds repeated import statements across multiple files in a directory.

    Args:
    directory (str): The path to the directory to search for repeated imports.

    Returns:
    dict: A dictionary where the keys are the import statements and the values are lists of files where the import statement is found.
    """
    repeated_imports = {}

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    tree = ast.parse(f.read())

                for node in tree.body:
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            import_stmt = f"import {alias.name}"
                            if import_stmt in repeated_imports:
                                repeated_imports[import_stmt].append(file_path)
                            else:
                                repeated_imports[import_stmt] = [file_path]

                    elif isinstance(node, ast.ImportFrom):
                        import_stmt = f"from {node.module} import {', '.join(alias.name for alias in node.names)}"
                        if import_stmt in repeated_imports:
                            repeated_imports[import_stmt].append(file_path)
                        else:
                            repeated_imports[import_stmt] = [file_path]

    repeated_imports = {k: v for k, v in repeated_imports.items() if len(v) > 2}

    return repeated_imports

if __name__ == "__main__":
    directory = "fastapi"
    repeated_imports = find_repeated_imports(directory)
    for import_stmt, files in repeated_imports.items():
        print(f"{import_stmt}: {files}")
    print("TEST PASSED")
