---
name: fastapi_oauth2_flow_skill
tags:
- fastapi
- security
- oauth2
- pattern
trigger: when constructing OAuth2 security flows in FastAPI applications
type: pattern
version: 1
success_count: 1
fail_count: 0
---
---
# FastAPI OAuth2 Flow Construction
## Purpose
To define and abstract the common pattern for setting up OAuth2 authentication in FastAPI applications. This skill covers the instantiation of OAuth2 security schemes and their integration into API endpoints.
## When to use
Use this skill when you need to implement OAuth2 authentication for your FastAPI application, specifically when you encounter or need to create code that sets up an `OAuth2PasswordBearer` (or similar OAuth2 scheme) and uses it as a dependency in route handlers.
## How to use
1. **Instantiate the Security Scheme:** Create an instance of `fastapi.security.OAuth2PasswordBearer` (or a custom OAuth2-compatible scheme). The most common parameter is `tokenUrl`, which specifies the endpoint for obtaining tokens.
   ```python
   from fastapi.security import OAuth2PasswordBearer

   oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
   ```
2. **Use as a Dependency:** In your FastAPI route functions, use the instantiated security scheme as a dependency using `Depends`. This dependency will automatically handle token extraction from the request (typically from the `Authorization` header).
   ```python
   from fastapi import Depends, FastAPI

   app = FastAPI()

   # ... (oauth2_scheme instantiation from step 1) ...

   @app.get("/protected-resource/")
   async def get_protected_resource(token: str = Depends(oauth2_scheme)):
       # The 'token' variable will contain the obtained access token
       # You can then proceed with token validation and authorization
       return {"message": "Access granted", "token": token}
   ```
3. **Token Validation (Outside this pattern):** While this skill focuses on the *construction* of the flow, remember that the extracted `token` will need to be validated by your application's logic (e.g., checking signature, expiry, scopes). This validation typically occurs within the route handler or a separate dependency function.