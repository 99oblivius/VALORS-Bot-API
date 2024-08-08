from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..services.discord_service import AuthService

router = APIRouter()

@router.get("/login")
async def login():
    return await AuthService.login()

@router.get("/callback")
async def callback(code: str, db: Session = Depends(get_db)):
    return await AuthService.callback(code, db)