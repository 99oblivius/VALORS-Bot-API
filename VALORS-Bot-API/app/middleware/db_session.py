from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        with request.app.state.db() as session:
            request.state.db = session
            response = await call_next(request)
        return response