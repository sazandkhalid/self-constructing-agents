# skill: starlette_reexport_lines
# version: 1
# tags: find, code, pattern, repeated, across
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T20:22:19.334637+00:00
# decaying: false
def starlette_reexport_lines(module_map: dict) -> list:
    """
    Generate starlette re-export import lines following the FastAPI convention.

    # protocol: general
    # rail: general
    # audit_required: false

    In the FastAPI repository, thin wrapper modules re-export Starlette symbols
    using the pattern:

        from starlette.<module> import <Symbol> as <Symbol>  # noqa: F401

    This exact pattern is present in at least these three source files:
      - fastapi/responses.py  (HTMLResponse, JSONResponse, Response, StreamingResponse, ...)
      - fastapi/websockets.py (WebSocket, WebSocketDisconnect)
      - fastapi/requests.py   (Request, HTTPConnection)
      - fastapi/background.py (BackgroundTasks)
      - fastapi/datastructures.py (UploadFile)
      - fastapi/staticfiles.py (StaticFiles)

    Args:
        module_map: dict mapping starlette sub-module name -> symbol name or list of names.
                    Example: {"responses": ["HTMLResponse", "JSONResponse"],
                              "websockets": "WebSocket"}

    Returns:
        List of import-line strings ready to write into a FastAPI wrapper .py file.
    """
    lines = []
    for starlette_module, symbols in module_map.items():
        if isinstance(symbols, str):
            symbols = [symbols]
        for sym in symbols:
            lines.append(
                f"from starlette.{starlette_module} import {sym} as {sym}  # noqa: F401"
            )
    return lines


if __name__ == "__main__":
    result = starlette_reexport_lines({
        "responses": ["HTMLResponse", "JSONResponse", "Response"],
        "websockets": ["WebSocket", "WebSocketDisconnect"],
        "requests": "Request",
        "background": "BackgroundTasks",
    })
    expected = [
        "from starlette.responses import HTMLResponse as HTMLResponse  # noqa: F401",
        "from starlette.responses import JSONResponse as JSONResponse  # noqa: F401",
        "from starlette.responses import Response as Response  # noqa: F401",
        "from starlette.websockets import WebSocket as WebSocket  # noqa: F401",
        "from starlette.websockets import WebSocketDisconnect as WebSocketDisconnect  # noqa: F401",
        "from starlette.requests import Request as Request  # noqa: F401",
        "from starlette.background import BackgroundTasks as BackgroundTasks  # noqa: F401",
    ]
    assert result == expected, f"Mismatch:\n" + "\n".join(result)
    print("TEST PASSED")
