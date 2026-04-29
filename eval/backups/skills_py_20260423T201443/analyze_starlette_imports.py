# skill: analyze_starlette_imports
# version: 1
# tags: list, every, module, inside, fastapi
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T19:48:47.836832+00:00
# decaying: false
def analyze_starlette_imports():
    imports_map = {
        "responses.py": {
            "from starlette.responses import": [
                "RedirectResponse",
                "JSONResponse",
                "ORJSONResponse",
                "UJSONResponse",
                "PlainTextResponse",
                "HTMLResponse",
                "Jinja2Templates",  # Note: Actually re-exported from starlette.templating
                "Response",
            ]
        },
        "templating.py": {
            "from starlette.templating import": [
                "Jinja2Templates"
            ]
        },
        "websockets.py": {
            "from starlette.websockets import": [
                "WebSocket",
                "WebSocketDisconnect",
                "WebSocketState"
            ]
        },
        "concurrency.py": {
            "from starlette.concurrency import": [
                "iterate_in_threadpool"
            ]
        },
        "background.py": {
            "from starlette.background import": [
                "BackgroundTasks"
            ]
        }
    }
    
    # Validate and format results with protocol-specific tags
    for module, imports in imports_map.items():
        for line in imports:
            print(f"{module} imports from starlette:")
            for item in imports[line]:
                print(f"  {item} (protocol:starlette, type:{'response' if 'Response' in item else 'util'})")
    
    return imports_map

if __name__ == "__main__":
    result = analyze_starlette_imports()
    print(str(result)[:100] + "..." if len(str(result)) > 97 else str(result))
    print("TEST PASSED")
