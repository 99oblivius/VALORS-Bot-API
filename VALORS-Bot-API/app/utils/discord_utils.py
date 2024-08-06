import httpx
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