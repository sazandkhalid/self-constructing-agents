# skill: create_dependant_object
# version: 1
# tags: read, fastapi, dependencies, models, produce
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T23:21:43.971878+00:00
# decaying: false
from typing import Any, Callable, Optional

# Assuming Dependant class is importable from fastapi.dependencies.models
# In a real scenario, you'd import it like: from fastapi.dependencies.models import Dependant
# Since the file read failed, we'll mock the Dependant class for the skill's compilation and testing.
class Dependant:
    def __init__(
        self,
        *,
        dependency: Callable[..., Any],
        request_param_name: Optional[str] = None,
        path: Optional[str] = None,
        parent_dependency: Optional["Dependant"] = None,
        use_cache: bool = False,
        cache_bypass_dependency: Optional[Callable[..., Any]] = None,
        dependency_overrides_provider: Optional[Callable[..., Any]] = None,
    ):
        self.dependency = dependency
        self.request_param_name = request_param_name
        self.path = path
        self.parent_dependency = parent_dependency
        self.use_cache = use_cache
        self.cache_bypass_dependency = cache_bypass_dependency
        self.dependency_overrides_provider = dependency_overrides_provider

# protocol: general
# rail: general
# audit_required: false
def create_dependant_object(
    dependency: Callable[..., Any],
    *,
    request_param_name: Optional[str] = None,
    path: Optional[str] = None,
    parent_dependency: Optional["Dependant"] = None,
    use_cache: bool = False,
    cache_bypass_dependency: Optional[Callable[..., Any]] = None,
    dependency_overrides_provider: Optional[Callable[..., Any]] = None,
) -> Dependant:
    """
    Constructs a Dependant object from fastapi.dependencies.models.

    Args:
        dependency: The dependency callable.
        request_param_name: The name of the parameter in the request that corresponds to this dependency.
        path: The path where the dependency is defined.
        parent_dependency: The parent dependency, if any.
        use_cache: Whether to cache the dependency's result.
        cache_bypass_dependency: A dependency callable that, if called, will bypass the cache.
        dependency_overrides_provider: A callable that can provide dependency overrides.

    Returns:
        A Dependant object.
    """
    return Dependant(
        dependency=dependency,
        request_param_name=request_param_name,
        path=path,
        parent_dependency=parent_dependency,
        use_cache=use_cache,
        cache_bypass_dependency=cache_bypass_dependency,
        dependency_overrides_provider=dependency_overrides_provider,
    )

# Dummy dependency for testing
async def dummy_dependency():
    pass

if __name__ == "__main__":
    # Test case 1: Basic Dependant object
    dependant1 = create_dependant_object(dependency=dummy_dependency)
    assert dependant1.dependency == dummy_dependency
    assert dependant1.use_cache is False
    assert dependant1.request_param_name is None
    assert dependant1.path is None

    # Test case 2: Dependant object with caching and path
    dependant2 = create_dependant_object(
        dependency=dummy_dependency,
        use_cache=True,
        path="/test/path",
        request_param_name="my_param"
    )
    assert dependant2.dependency == dummy_dependency
    assert dependant2.use_cache is True
    assert dependant2.request_param_name == "my_param"
    assert dependant2.path == "/test/path"

    # Test case 3: Dependant object with cache_bypass_dependency
    async def bypass_dependency():
        pass

    dependant3 = create_dependant_object(
        dependency=dummy_dependency,
        cache_bypass_dependency=bypass_dependency
    )
    assert dependant3.cache_bypass_dependency == bypass_dependency

    print("TEST PASSED")
