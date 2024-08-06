import random
from fastapi import Request
from fastapi.responses import JSONResponse
from ..utils.logger import log

async def handle_data(request: Request):
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "origin": request.headers.get("Origin"),
        "client": request.client.host,
        "user_agent": request.headers.get("User-Agent")
    }
    log.info(f"Data request received: {request_info}")
    response_data = {"number": random.randrange(100)}
    return JSONResponse(content=response_data)