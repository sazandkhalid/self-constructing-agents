---
name: contextmanager_to_async_skill
tags:
- asyncio
- context-manager
- utility
trigger: when needing to use a synchronous context manager within an asynchronous
  context
type: pattern
version: 1
success_count: 1
fail_count: 0
---
---
# Context Manager to Async Skill
## Purpose
This skill provides a utility function to convert a synchronous context manager into an asynchronous context manager. This allows synchronous resources to be used seamlessly within `async with` statements in asynchronous Python applications.
## When to use
Use this skill when you have a synchronous context manager (a class with `__enter__` and `__exit__` methods) and need to use it within an `async def` function using `async with`. This is particularly useful when integrating legacy synchronous libraries into modern asynchronous frameworks like FastAPI or Starlette.
## How to use
1. Import the `contextmanager_to_async` function.
2. Define your synchronous context manager class.
3. Use `contextmanager_to_async` to wrap your synchronous context manager instance, creating an asynchronous context manager.
4. Use the resulting asynchronous context manager with `async with`.

Example:

```python
import contextlib

# Assume this is a synchronous context manager
class SyncFileManager:
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode
        self.file = None

    def __enter__(self):
        print(f"Opening file {self.filename} in mode {self.mode}")
        self.file = open(self.filename, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Closing file {self.filename}")
        if self.file:
            self.file.close()
        if exc_type:
            print(f"An exception occurred: {exc_val}")
        return False # Re-raise exceptions

# --- Using the skill ---
from contextlib import contextmanager # Assuming contextmanager_to_async is available

@contextmanager # This decorator is for illustrative purposes; the skill handles the conversion
def contextmanager_to_async(sync_context_manager_instance):
    class AsyncContextManager:
        async def __aenter__(self):
            return sync_context_manager_instance.__enter__()

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return sync_context_manager_instance.__exit__(exc_type, exc_val, exc_tb)
    return AsyncContextManager()

async def main():
    sync_file_manager = SyncFileManager("my_file.txt", "w")
    async_file_manager = contextmanager_to_async(sync_file_manager)

    async with async_file_manager as f:
        f.write("Hello from async context!")
        print("Inside async with block.")

    print("Outside async with block.")

# To run this example:
# import asyncio
# asyncio.run(main())
```