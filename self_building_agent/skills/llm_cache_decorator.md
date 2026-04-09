---
name: llm_cache_decorator
tags:
- caching
- llm
- api
- performance
- decorator
- python
trigger: task involves caching LLM responses or avoiding repeated API calls
type: pattern
version: 1
success_count: 0
fail_count: 1
---
# LLM Cache Decorator
## Purpose
Provide a Python decorator that caches Large Language Model responses to disk to reduce redundant API calls.

## When to use
Use this decorator when you need to optimize performance by avoiding redundant LLM API calls, especially when the same prompts are submitted multiple times.

## How to use
1. **Implement the Decorator**: Use the code below to create the decorator.
2. **Apply the Decorator**: Wrap your LLM call function with `@llm_cache()`.
3. **Configure Cache Directory**: Optionally specify a custom cache directory.

### Example Code
```python
import os, hashlib, pickle
from functools import wraps

def llm_cache(cache_dir='./llm_cache'):
    def decorator(func):
        @wraps(func)
        def wrapper(prompt, *args, **kwargs):
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
            cache_file = os.path.join(cache_dir, f'{prompt_hash}.pickle')
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as file:
                    return pickle.load(file)
            response = func(prompt, *args, **kwargs)
            os.makedirs(cache_dir, exist_ok=True)
            with open(cache_file, 'wb') as file:
                pickle.dump(response, file)
            return response
        return wrapper
    return decorator
```

### Tips
- Regularly clean up the cache directory to avoid stale responses.
- Consider implementing a TTL for cache entries.