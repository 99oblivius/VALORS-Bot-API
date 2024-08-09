from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class AsyncDBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        async with request.app.state.AsyncSessionLocal() as session:
            request.state.db = session
            try:
                response = await call_next(request)
                await session.commit()
                return response
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()