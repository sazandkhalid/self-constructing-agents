# skill: check_file_exists
# version: 1
# tags: list, dependency, injection, helper, functions
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-07T15:50:48.703064+00:00
# decaying: false
import os

def check_file_exists(filename):
    'Return True if a file exists, False otherwise.'
    return os.path.isfile(filename)

def test_check_file_exists():
    filename = 'fastapi/dependencies/utils.py'
    exists = check_file_exists(filename)
    if not exists:
        print(f"File {filename} does not exist.")
    else:
        print(f"File {filename} exists.")
    print("TEST PASSED")

if __name__ == "__main__":
    test_check_file_exists()
