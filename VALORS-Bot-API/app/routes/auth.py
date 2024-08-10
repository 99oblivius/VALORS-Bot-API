import hmac
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from config import config
from ..models import User
from ..services.login_session_manager import LoginSessionManager
from ..utils.database import get_db
from ..services.discord_service import AuthService

router = APIRouter()

@router.get("/login")
async def login():
    return await AuthService.login()

@router.get("/callback")
async def callback(request: Request):
    error = request.query_params.get('error')
    code = request.query_params.get('code')
    if error or not code:
        return RedirectResponse(url="https://valorsleague.org/")
    return await AuthService.callback(code, request)

@router.get("/check-session")
async def check_session(request: Request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise HTTPException(status_code=401, detail={"error": "Missing Authorization header"})
    
    if not hmac.compare_digest(auth_header, config.API_KEY):
        raise HTTPException(status_code=401, detail={"error": "Invalid token"})
    
    session_token = request.query_params.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail={"error": "No session token"})

    session_manager = LoginSessionManager(request.state.db)
    session = session_manager.get_session(session_token)
    if not session:
        raise HTTPException(status_code=401, detail={"error": "Invalid session"})

    return {"success": "Logged In"}