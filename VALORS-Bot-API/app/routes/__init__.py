from fastapi import APIRouter, Request
from ..utils.database import get_db
from ..services import auth_service, update_service, data_service
from .auth import router as auth_router
from .match_making import router as mm_router
from .discord import router as guild_router
from .users import router as user_router
from .teams import router as teams_router

router = APIRouter()

def init_routes(app):
    router.include_router(auth_router, prefix="/session", tags=["authentication"])
    router.include_router(user_router, prefix="/user", tags=["user"])
    router.include_router(teams_router, prefix="/team", tags=["team"])
    router.include_router(guild_router, prefix="/guild", tags=["discord"])
    router.include_router(mm_router, prefix="/matchmaking", tags=["matchmaking"])

    @router.post('/update')
    async def update(request: Request):
        return await update_service.handle_update(request)

    @router.get('/mm-auth/{platform}/{token}')
    async def auth(platform: str, token: str, request: Request):
        return await auth_service.handle_auth(request, platform, token)

    @router.get('/verify')
    async def verify(request: Request):
        return await auth_service.handle_verify(request)

    @router.get('/verified')
    async def verified(request: Request):
        return await auth_service.handle_verified(request)

    @router.get('/data')
    async def data(request: Request):
        return await data_service.handle_data(request)

    app.include_router(router)