import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .models import init_db
from .routes import init_routes
import aioredis
from datetime import datetime, timezone
from .utils.logger import log
from config import config

def create_app():
    app = FastAPI()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://valorsleague.org"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"])

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    
    # Set logger level
    log.set_level(log.DEBUG if app.debug else log.INFO)
    
    # Initialize database
    init_db(app)
    
    # Initialize Redis
    app.redis_db = aioredis.from_url(f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}", decode_responses=True)
    
    # Initialize routes
    init_routes(app)
    
    log.info(f"Server started at {datetime.now(timezone.utc)}")
    
    return app