from fastapi import FastAPI
from .models import init_db, init_models
from .routes import init_routes
import aioredis
from datetime import datetime, timezone
from .utils.logger import log
from config import config
from .middleware.db_session import AsyncDBSessionMiddleware
from .middleware.cors import add_cors_middleware
from .middleware.exception_handler import add_exception_handler

def create_app() -> FastAPI:
    app = FastAPI()
    
    # Add middlewares
    add_cors_middleware(app)
    add_exception_handler(app)
    
    # Set logger level
    log.set_level(log.DEBUG if app.debug else log.INFO)
    
    # Initialize database
    @app.on_event("startup")
    async def startup_event():
        await init_db(app)
        await init_models(app.state.engine)
    
    # Add DB Session Middleware
    app.add_middleware(AsyncDBSessionMiddleware)
    
    # Initialize Redis
    app.redis_db = aioredis.from_url(f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}", decode_responses=True)
    
    # Initialize routes
    init_routes(app)
    
    log.info(f"Server started at {datetime.now(timezone.utc)}")
    
    return app