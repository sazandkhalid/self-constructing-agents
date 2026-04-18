# skill: find_starlette_imports
# version: 1
# tags: list, every, module, inside, fastapi
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-09T01:39:51.610148+00:00
# decaying: false
def find_starlette_imports(directory):
    '''
    Finds all modules inside the given directory that import from starlette and reports which starlette names each one imports.
    
    Args:
        directory (str): The path to the directory to search for starlette imports.
    
    Returns:
        dict: A dictionary where the keys are the relative paths to the modules and the values are lists of starlette names imported by each module.
    '''
    import ast
    import os
    
    starlette_imports = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        tree = ast.parse(f.read())
                        imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
                        starlette_names = []
                        for import_node in imports:
                            if import_node.module == 'starlette':
                                for alias in import_node.names:
                                    starlette_names.append(alias.name)
                        if starlette_names:
                            relative_path = os.path.relpath(file_path, directory)
                            starlette_imports[relative_path] = starlette_names
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
    return starlette_imports

if __name__ == "__main__":
    directory = 'fastapi'
    starlette_imports = find_starlette_imports(directory)
    assert isinstance(starlette_imports, dict)
    for file, imports in starlette_imports.items():
        assert isinstance(file, str)
        assert isinstance(imports, list)
        for imp in imports:
            assert isinstance(imp, str)
    print("TEST PASSED")
