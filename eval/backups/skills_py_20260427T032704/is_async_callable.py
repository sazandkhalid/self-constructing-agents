# skill: is_async_callable
# version: 1
# tags: look, fastapi, utils, extract, small
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T23:20:23.310796+00:00
# decaying: false
def is_async_callable(value: Any) -> bool:
    'Check if a value is an asynchronous callable (coroutine function or async generator function).'
    import inspect
    return inspect.isasyncgenfunction(value) or inspect.iscoroutinefunction(value)

if __name__ == "__main__":
    async def async_func():
        pass
    def sync_func():
        pass
    class AsyncClass:
        async def async_method(self):
            pass
    class SyncClass:
        def sync_method(self):
            pass
    
    assert is_async_callable(async_func) == True
    assert is_async_callable(sync_func) == False
    assert is_async_callable(AsyncClass().async_method) == True
    assert is_async_callable(SyncClass().sync_method) == False
    assert is_async_callable(None) == False
    assert is_async_callable(123) == False
    print("TEST PASSED")
