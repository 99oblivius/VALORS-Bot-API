from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..models import User
from ..services.session_manager import SessionManager
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
    return await AuthService.callback(code, db, request)

@router.get("/check-session")
async def check_session(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_manager = SessionManager(db)
    session = session_manager.get_session(session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "roles": [role.name for role in user.roles]
    }