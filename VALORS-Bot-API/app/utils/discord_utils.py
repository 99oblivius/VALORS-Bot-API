import requests
from config import DISCORD_API_ENDPOINT, DISCORD_BOT_TOKEN

def add_discord_role(guild_id, user_id, role_id):
    url = f"{DISCORD_API_ENDPOINT}/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
    headers = {
        'Authorization': f'Bot {DISCORD_BOT_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    response = requests.put(url, headers=headers)
    return response.status_code == 204