import hmac
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from config import config
from ..services.login_session_manager import SessionManager
from ..utils.database import get_db
from ..services.sessions import Sessions

router = APIRouter()

@router.post("/create")
async def create_session(request: Request):
    return await Sessions.login(request)

@router.get("/check")
async def check_session(request: Request):
    auth_header = request.headers.get('Authorization', None)
    if not auth_header:
        raise HTTPException(status_code=401, detail={"error": "Missing Authorization header"})
    
    if not hmac.compare_digest(auth_header, config.API_TOKEN):
        raise HTTPException(status_code=401, detail={"error": "Invalid token"})
    
    session_token = request.headers.get('session-token', None)
    if not session_token:
        raise HTTPException(status_code=401, detail={"error": "No session token"})

    session = await SessionManager.fetch(request.state.db, session_token)
    if not session:
        raise HTTPException(status_code=401, detail={"error": "Invalid session"})

    return JSONResponse(status_code=200, content={"success": "Logged In"})