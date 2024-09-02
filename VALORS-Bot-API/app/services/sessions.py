import hmac
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from ..utils.discord import get_user_info
from ..utils.logger import log
from ..models import User
from ..utils.database import upsert_user
from .login_session_manager import LoginSessionManager
from config import config

class Sessions:
    @staticmethod
    async def login(request: Request):
        auth_header = request.headers.get('Authorization', None)
        if auth_header is None:
            raise HTTPException(status_code=401, detail={"error": "Missing Authorization header"})
        
        if not hmac.compare_digest(auth_header, config.API_TOKEN):
            raise HTTPException(status_code=401, detail={"error": "Invalid token"})

        access_token = request.headers.get('access-token', None)
        if access_token is None:
            raise HTTPException(status_code=400, detail={"error": "Missing access token"})
    
        try:
            user_info = await get_user_info(access_token)
            if 'id' not in user_info:
                raise HTTPException(status_code=400, detail={"error": "Failed to get user info"})
        except Exception:
            raise HTTPException(status_code=500, detail={"error": "Something went wrong during user login"})
            
        try:
            user = await upsert_user(request.state.db, 
                discord_id=user_info['id'], 
                email=user_info['email'],
                username=user_info['username'])
        except Exception:
            raise HTTPException(status_code=500, detail={"error": "Failed to upsert user info"})

        try:
            session_manager = LoginSessionManager(request.state.db)
            session = await session_manager.create_session(
                user, 
                ip_address=request.headers.get("address", ""), 
                user_agent=request.headers.get("client-agent", ""))
        except Exception:
            raise HTTPException(status_code=500, detail={"error": "Something went wrong during user session creation"})
        
        log.info(f"Login info posted for {user_info['id']}")
        return JSONResponse(status_code=200, content={'session_token': session.session_token})
