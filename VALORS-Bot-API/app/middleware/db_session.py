from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session = request.app.state.db()
        request.state.db = session
        try:
            response = await call_next(request)
            return response
        finally:
            session.close()