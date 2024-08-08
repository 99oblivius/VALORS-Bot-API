from config import config
import httpx

DISCORD_API_URL = "https://discord.com/api"

async def get_discord_token(code: str):
    data = {
        'client_id': config.DISCORD_CLIENT_ID,
        'client_secret': config.DISCORD_CLIENT_TOKEN,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': config.DISCORD_REDIRECT_URI
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f'{DISCORD_API_URL}/oauth2/token', data=data)
    return response.json()

async def get_discord_user(access_token: str):
    headers = {'Authorization': f'Bearer {access_token}'}
    async with httpx.AsyncClient() as client:
        response = await client.get(f'{DISCORD_API_URL}/users/@me', headers=headers)
    return response.json()