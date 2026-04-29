# skill: example_dependency
# version: 1
# tags: write, depends, style, helper, named
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-07T15:52:21.957719+00:00
# decaying: false
class DependsCached:
    def __init__(self, dependency: Callable, cache: bool = True):
        self.dependency = dependency
        self.cache = cache
        self.cache_dict = {}

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        key = (args, frozenset(kwargs.items()))
        if key in self.cache_dict:
            return self.cache_dict[key]
        result = self.dependency(*args, **kwargs)
        self.cache_dict[key] = result
        return result

    def __repr__(self) -> str:
        return f"DependsCached(dependency={self.dependency}, cache={self.cache})"

def example_dependency(x: int, y: int) -> int:
    import time
    time.sleep(1)
    return x + y

DependsCachedExample = DependsCached(example_dependency)

def main():
    print(DependsCachedExample(1, 2))  
    print(DependsCachedExample(1, 2))  

    assert DependsCachedExample(1, 2) == 3
    print("TEST PASSED")

if __name__ == "__main__":
    main()
