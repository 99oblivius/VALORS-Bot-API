import requests
import os

def add_discord_role(guild_id, user_id, role_id):
    url = f"{os.getenv('DISCORD_API_ENDPOINT')}/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
    headers = {
        'Authorization': f'Bot {os.getenv("DISCORD_BOT_TOKEN")}',
        'Content-Type': 'application/json'
    }
    
    response = requests.put(url, headers=headers)
    return response.status_code == 204