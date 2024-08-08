from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..utils.discord import exchange_code, get_user_info
from ..models import UserPlatformMappings
from config import config

class AuthService:
    @staticmethod
    async def login():
        url = f"https://discord.com/api/oauth2/authorize?client_id={config.DISCORD_CLIENT_ID}&redirect_uri={config.DISCORD_REDIRECT_URI}&response_type=code&scope=identify+email"
        return RedirectResponse(url=url)

    @staticmethod
    async def callback(code: str, db: Session):
        token_data = await exchange_code(code)
        if 'access_token' not in token_data:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        user_info = await get_user_info(token_data['access_token'])
        if 'id' not in user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")
    
        # user = db.query(UserPlatformMappings).filter_by(user_id=int(user_info['id']), platform='discord').first()
        # if not user:
        #     user = UserPlatformMappings(
        #         user_id=int(user_info['id']),
        #         platform='discord',
        #         platform_id=user_info['id']
        #     )
        #     db.add(user)
        #     db.commit()

        # Here you would typically create a session for the user
        # For now, we'll just return the user info
        print(user_info)
        return user_info