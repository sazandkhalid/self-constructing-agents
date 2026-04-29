# skill: get_api_key
# version: 1
# tags: write, small, fastapi, security, scheme
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-07T15:53:22.671389+00:00
# decaying: false
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.testclient import TestClient

app = FastAPI()

def get_api_key(request: Request):
    api_key = request.query_params.get("api_key")
    if not api_key:
        raise HTTPException(status_code=403, detail="API key not found in query parameters")
    return api_key

@app.get("/test")
async def test(api_key: str = Depends(get_api_key)):
    return {"api_key": api_key}

def test_api_key_query_security():
    client = TestClient(app)
    response = client.get("/test?api_key=example_key")
    assert response.status_code == 200
    assert response.json() == {"api_key": "example_key"}
    response = client.get("/test")
    assert response.status_code == 403
    assert "API key not found in query parameters" in response.text
    print("TEST PASSED")

if __name__ == "__main__":
    test_api_key_query_security()
