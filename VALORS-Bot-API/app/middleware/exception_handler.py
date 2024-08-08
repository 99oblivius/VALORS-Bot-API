from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

def add_exception_handler(app):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)