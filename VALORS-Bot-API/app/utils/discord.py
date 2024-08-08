import httpx
import aiohttp
from config import config

async def add_discord_role(guild_id, user_id, role_id):
    url = f"{config.DISCORD_API_ENDPOINT}/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
    headers = {
        'Authorization': f'Bot {config.DISCORD_BOT_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers)
    return response.status_code == 204

async def exchange_code(code: str):
    data = {
        'client_id': config.DISCORD_CLIENT_ID,
        'client_secret': config.DISCORD_CLIENT_TOKEN,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': config.DISCORD_REDIRECT_URI
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{config.DISCORD_API_ENDPOINT}/oauth2/token', data=data, headers=headers) as resp:
            return await resp.json()

async def get_user_info(access_token: str):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{config.DISCORD_API_ENDPOINT}/users/@me', headers=headers) as resp:
            return await resp.json()