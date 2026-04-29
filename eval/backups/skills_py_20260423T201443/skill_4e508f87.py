# skill: skill_4e508f87
# version: 1
# tags: write, apiroute, subclass, follows, constructor
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T19:52:09.809182+00:00
# decaying: false
from fastapi.routing import APIRoute

class CustomTagRoute(APIRoute):
    """APIRoute subclass with an additional custom_tag attribute."""
    
    def __init__(self, *args, custom_tag: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_tag = custom_tag

if __name__ == "__main__":
    # Test creation with standard attributes and custom tag
    test_route = CustomTagRoute(
        path="/test",
        endpoint=lambda: None,
        methods=["GET"],
        custom_tag="processing"
    )
    
    assert hasattr(test_route, "custom_tag"), "Missing custom_tag attribute"
    assert test_route.custom_tag == "processing", "Custom tag value mismatch"
    print("TEST PASSED")
