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
    return JSONResponse(status_code=200, content={"success": "Logged In"})