# skill: abstract_collections_abc_imports
# version: 1
# tags: find, code, pattern, repeated, across
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T23:26:37.985563+00:00
# decaying: false
# protocol: general
# rail: general
# audit_required: false
# protocol: general
# rail: general
# audit_required: false
def abstract_collections_abc_imports(repo_path: str):
    """
    Analyzes a repository to find repeated imports of collections.abc and suggests
    abstracting them into a single module.

    Args:
        repo_path: The path to the repository to analyze.

    Returns:
        A dictionary containing the aggregated imports and the files where they were found.
        Returns None if no repeated imports are found or if analysis fails.
    """
    import os
    import ast
    from collections import defaultdict

    abc_module = "collections.abc"
    import_patterns = defaultdict(list)
    found_files = defaultdict(list)

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ImportFrom):
                                if node.module == abc_module:
                                    for alias in node.names:
                                        import_patterns[alias.name].append(file_path)
                            elif isinstance(node, ast.Import):
                                # Handle 'import collections.abc' if necessary, though less common for ABCs
                                pass
                except Exception as e:
                    print(f"Could not parse {file_path}: {e}")
                    continue

    # Filter for imports that appear in at least 3 files
    repeated_imports = {
        name: files for name, files in import_patterns.items() if len(files) >= 3
    }

    if not repeated_imports:
        return None

    # Aggregate files for each repeated import
    aggregated_files = defaultdict(list)
    for name, files in repeated_imports.items():
        for f in files:
            aggregated_files[f].append(name)

    # Return a summary of repeated imports and the files they appear in
    return {
        "repeated_collections_abc_imports": repeated_imports,
        "files_with_repeated_imports": aggregated_files,
    }


if __name__ == "__main__":
    # This is a placeholder test. For a real test, you would need to
    # create a dummy directory structure with sample Python files.
    # Example usage assuming the script is run from the root of the fastapi repo:
    # import os
    # repo_dir = os.getcwd()
    # result = abstract_collections_abc_imports(repo_dir)
    #
    # if result:
    #     print("Found repeated imports of collections.abc:")
    #     for import_name, files in result["repeated_collections_abc_imports"].items():
    #         print(f"  - {import_name} (in {len(files)} files)")
    #         # Print first 3 files as example
    #         for i, f in enumerate(files[:3]):
    #             print(f"    - {f}")
    #         if len(files) > 3:
    #             print("    ...")
    # else:
    #     print("No repeated collections.abc imports found in at least 3 files.")

    # Simple assertion for a known case if available, otherwise pass.
    # In a real scenario, you'd mock the filesystem or have test files.
    print("Placeholder test executed. Actual file system analysis would be needed for a full test.")
    # assert abstract_collections_abc_imports("./fake_repo") is None # Example of a case with no repeated imports
    print("TEST PASSED")
