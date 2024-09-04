import hmac
from fastapi import APIRouter, Request, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from ..utils.database import get_user_roles, get_user, get_user_from_session
from sqlalchemy.ext.asyncio import AsyncSession
from config import config
from ..services.login_session_manager import SessionManager

router = APIRouter()

@router.get("/me")
async def user_info(request: Request, user_id: int = Query(None, alias="user")):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise HTTPException(status_code=401, detail={"error": "Missing Authorization header"})
    
    if not hmac.compare_digest(auth_header, config.API_TOKEN):
        raise HTTPException(status_code=401, detail={"error": "Invalid token"})

    session_token = request.headers.get('session-token', None)
    session = await SessionManager.fetch(request.state.db, session_token)
    if session_token:
        if not session:
            raise HTTPException(status_code=401, detail={"error": "Invalid session token"})
        user = await get_user_from_session(request.state.db, session_token)
    else:
        user = await get_user(request.state.db, user_id)
    
    user_roles = await get_user_roles(request.state.db, user.discord_id)
    
    response_data = {
        "id": user.id, 
        "discord_id": user.discord_id, 
        "username": user.username, 
        "email": user.email, 
        "roles": [role.role.value for role in user_roles],
        "is_active": user.is_active
    }
    return JSONResponse(status_code=200, content={'user': response_data})