import hmac
import re

from config import config
from fastapi import Request
from fastapi.responses import JSONResponse
from ..services.sessions import SessionManager
from ..utils.database import get_user_roles

from starlette.middleware.base import BaseHTTPMiddleware


class SessionTokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, whitelist_patterns):
        super().__init__(app)
        self.whitelist_patterns = [re.compile(pattern) for pattern in whitelist_patterns]
    
    async def dispatch(self, request: Request, call_next):
        if any(pattern.match(request.url.path) for pattern in self.whitelist_patterns):
            token = request.headers.get('session-token', None)
            if not token:
                return JSONResponse(status_code=401, content={"error": "Missing User Session token"})
            
            async with request.app.state.AsyncSessionLocal() as session:
                user_session = await SessionManager.fetch(session, token)
                if not user_session:
                    return JSONResponse(status_code=401, content={"error": "Invalid User Session token"})
                request.state.roles = await get_user_roles(session, user_session.user_id)
                request.state.user_id = user_session.user_id
        return await call_next(request)


class AuthorizationTokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, whitelist_patterns):
        super().__init__(app)
        self.whitelist_patterns = [re.compile(pattern) for pattern in whitelist_patterns]
    
    async def dispatch(self, request: Request, call_next):
        if any(pattern.match(request.url.path) for pattern in self.whitelist_patterns):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return JSONResponse(status_code=401, content={"error": "Missing Authorization header"})
            
            if not hmac.compare_digest(auth_header, config.API_TOKEN):
                return JSONResponse(status_code=401, content={"error": "Invalid Authorization token"})
        return await call_next(request)