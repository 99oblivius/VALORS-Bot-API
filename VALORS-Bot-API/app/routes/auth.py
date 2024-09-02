import hmac
from fastapi import APIRouter, Request, HTTPException
from config import config
from ..services.login_session_manager import LoginSessionManager
from ..utils.database import get_db
from ..services.sessions import Sessions

router = APIRouter()

@router.post("/create")
async def create_session(request: Request):
    return await Sessions.login(request)

@router.get("/check")
async def check_session(request: Request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise HTTPException(status_code=401, detail={"error": "Missing Authorization header"})
    
    if not hmac.compare_digest(auth_header, config.API_TOKEN):
        raise HTTPException(status_code=401, detail={"error": "Invalid token"})
    
    session_token = request.query_params.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail={"error": "No session token"})

    session_manager = LoginSessionManager(request.state.db)
    session = session_manager.get_session(session_token)
    if not session:
        raise HTTPException(status_code=401, detail={"error": "Invalid session"})

    return {"success": "Logged In"}