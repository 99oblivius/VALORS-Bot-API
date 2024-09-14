from fastapi import FastAPI
from .models import init_db, init_models
from .discord import init_discord
from .routes import init_routes
import aioredis
from datetime import datetime, timezone
from .utils.logger import log
from config import config
from .middleware import (
    AsyncDBSessionMiddleware, 
    SessionTokenMiddleware, AuthorizationTokenMiddleware, 
    add_cors_middleware, 
    add_exception_handler
)

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
        await init_db(app, config.DATABASE_URL)
        await init_models(app.state.engine)
        await init_discord()
    
    # Add DB Session Middleware
    app.add_middleware(AsyncDBSessionMiddleware)

    # Add Authorization Middleware
    app.add_middleware(AuthorizationTokenMiddleware, 
        whitelist_patterns=[
            r"^/user",
            r"^/team",
            r"^/session",
            r"^/guild",
            r"^/matchmaking"
        ])

    # Add Session Token Middleware
    app.add_middleware(SessionTokenMiddleware, 
        whitelist_patterns=[
            r"^/user/me",
            r"^/user/roles",
            r"^/user/all",
            r"^/user/\d+",
            
            r"^/team/update",
            r"^/team/join-request",
            r"^/team/",
            r"^/team/\d+/kick",
            
            r"^/session/check"
        ])
    
    # Initialize Redis
    app.redis_db = aioredis.from_url(f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}", decode_responses=True)
    
    # Initialize routes
    init_routes(app)
    
    log.info(f"Server started at {datetime.now(timezone.utc)}")
    
    return app