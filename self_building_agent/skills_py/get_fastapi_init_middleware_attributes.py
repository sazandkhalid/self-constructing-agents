# skill: get_fastapi_init_middleware_attributes
# version: 1
# tags: trace, fastapi, applications, __init__, list
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T23:17:21.823598+00:00
# decaying: false
import ast

# protocol: general
# rail: general
# audit_required: false
def get_fastapi_init_middleware_attributes(file_content: str) -> list[str]:
    """
    Parses the content of fastapi/applications.py to find middleware-related
    attribute names within the FastAPI.__init__ method.

    It looks for assignments to 'self.attribute_name' where the attribute name
    or the assigned value suggests a connection to middleware.
    """
    middleware_attributes = set()
    tree = ast.parse(file_content)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'FastAPI':
            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef) and body_item.name == '__init__':
                    for statement in ast.walk(body_item):
                        # Detect assignments like: self.middleware = [...] or self.middleware_list = [...]
                        if isinstance(statement, ast.Assign):
                            for target in statement.targets:
                                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                    attr_name = target.attr
                                    # Heuristic 1: Attribute name contains 'middleware'
                                    if 'middleware' in attr_name.lower():
                                        middleware_attributes.add(attr_name)

                                    # Heuristic 2: Assigned value is a list/tuple that might contain middleware
                                    # e.g., middleware = [Middleware(...), ...]
                                    if isinstance(statement.value, (ast.List, ast.Tuple)):
                                        for element in statement.value.elts:
                                            if isinstance(element, ast.Call) and isinstance(element.func, ast.Name):
                                                # Checks for common middleware classes like Starlette's Middleware
                                                if 'Middleware' in element.func.id:
                                                    # If a list/tuple is assigned, and it contains middleware,
                                                    # then the attribute holding this list is middleware-related.
                                                    middleware_attributes.add(attr_name)
                                            elif isinstance(element, ast.Name):
                                                # Handle cases where a variable name holding middleware is assigned
                                                if 'Middleware' in element.id:
                                                    middleware_attributes.add(attr_name)
                                    # Heuristic 3: Assigned value is a direct call to a Middleware constructor
                                    elif isinstance(statement.value, ast.Call) and isinstance(statement.value.func, ast.Name) and 'Middleware' in statement.value.func.id:
                                        middleware_attributes.add(attr_name)
    return sorted(list(middleware_attributes))

if __name__ == "__main__":
    # Mock file content for testing the skill locally
    mock_file_content = """
import typing
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.types import ASGIApp

from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRouter

# Some dummy code to make ast parsing work without errors
class MockMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)

class FastAPI(Starlette):
    def __init__(
        self,
        *,
        routes: typing.Optional[typing.List[typing.Union[Route, APIRouter]]] = None,
        middleware: typing.Optional[typing.List[typing.Union[Middleware, tuple]]] = None,
        exception_handlers: typing.Optional[typing.Dict[typing.Any, typing.Callable]] = None,
        on_startup: typing.Optional[typing.List[typing.Callable]] = None,
        on_shutdown: typing.Optional[typing.List[typing.Callable]] = None,
        debug: bool = False,
        root_path: str = "",
        default_response_class: typing.Type[Response] = Response,
        middleware_list: typing.List[Middleware] = [], # another middleware attribute
        other_stuff: str = "hello",
        custom_middleware_handler: ASGIApp = None, # another one
        custom_middleware: typing.List[MockMiddleware] = [MockMiddleware(None)] # another one with custom class
    ) -> None:
        self.routes = routes
        self.exception_handlers = exception_handlers
        self.on_startup = on_startup
        self.on_shutdown = on_shutdown
        self.debug = debug
        self.root_path = root_path
        self.default_response_class = default_response_class
        self.middleware = middleware if middleware is not None else []
        self.middleware_list = middleware_list
        self.other_stuff = other_stuff
        self.custom_middleware_handler = custom_middleware_handler
        self.custom_middleware = custom_middleware # assignment of custom_middleware
        super().__init__(routes=routes,
                         middleware=self.middleware,
                         exception_handlers=exception_handlers,
                         on_startup=on_startup,
                         on_shutdown=on_shutdown,
                         debug=debug,
                         root_path=root_path,
                         default_response_class=default_response_class)

"""
    attributes = get_fastapi_init_middleware_attributes(mock_file_content)
    assert attributes == ['custom_middleware', 'custom_middleware_handler', 'middleware', 'middleware_list'], f"Expected ['custom_middleware', 'custom_middleware_handler', 'middleware', 'middleware_list'], but got {attributes}"
    print("TEST PASSED")
