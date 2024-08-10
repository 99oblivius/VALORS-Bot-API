from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from ..utils.discord import exchange_code, get_user_info, revoke_token
from ..models import User
from ..utils.database import upsert_user
from .login_session_manager import LoginSessionManager
from config import config

class AuthService:
    @staticmethod
    async def login():
        url = f"https://discord.com/api/oauth2/authorize?client_id={config.DISCORD_CLIENT_ID}&redirect_uri={config.DISCORD_REDIRECT_URI}&response_type=code&scope=identify+email"
        return RedirectResponse(url=url)

    @staticmethod
    async def callback(code: str, request: Request):
        token_data = await exchange_code(code)
        if 'access_token' not in token_data:
            raise HTTPException(status_code=400, detail={"error": "Failed to get access token"})
        
        user_info = await get_user_info(token_data['access_token'])
        if 'id' not in user_info:
            raise HTTPException(status_code=400, detail={"error": "Failed to get user info"})
        
        await revoke_token(token_data['access_token'])

        user = await upsert_user(request.state.db, 
            discord_id=user_info['id'], 
            email=user_info['email'],
            username=user_info['username'])
        
        session_manager = LoginSessionManager(request.state.db)
        session = await session_manager.create_session(
            user, 
            ip_address=request.client.host, 
            user_agent=request.headers.get("user-agent", ""))

        response = RedirectResponse(url="https://valorsleague.org/profile/")
        response.set_cookie(
            key="session_token", 
            value=session.session_token, 
            httponly=True,
            # secure=True,
            )

        return response