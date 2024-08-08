from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..services.discord_service import AuthService

router = APIRouter()

@router.get("/login")
async def login():
    return await AuthService.login()

@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    error = request.query_params.get('error')
    code = request.query_params.get('code')
    if error or not code:
        return RedirectResponse(url="https://valorsleague.org/")
    return await AuthService.callback(code, db)