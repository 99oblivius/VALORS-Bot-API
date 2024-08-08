from fastapi import APIRouter, Request, Depends
from ..dependencies import get_db
from sqlalchemy.orm import Session
from ..services import auth_service, update_service, data_service

router = APIRouter()

def init_routes(app):
    @router.post('/update')
    async def update(request: Request):
        return await update_service.handle_update(request)

    @router.get('/auth/{platform}/{token}')
    async def auth(platform: str, token: str, request: Request):
        return await auth_service.handle_auth(request, platform, token)

    @router.get('/verify')
    async def verify(request: Request, db: Session = Depends(get_db)):
        return await auth_service.handle_verify(request, db)

    @router.get('/verified')
    async def verified(request: Request):
        return await auth_service.handle_verified(request)

    @router.get('/data')
    async def data(request: Request):
        return await data_service.handle_data(request)

    app.include_router(router)