import time
import json

from aioredis import Redis
import nextcord
from datetime import datetime
from config import config
from ..utils.logger import log

class DiscordClient(nextcord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.guild = None
        self.AVATAR_CACHE_TTL = 24 * 60 * 60  # 24 hours in seconds
        self.AVATAR_UPDATE_INTERVAL = 24 * 60 * 60  # 24 hours in seconds

    async def on_ready(self):
        self.guild = self.get_guild(config.DISCORD_GUILD_ID)
        if self.guild:
            log.info(f'Logged in as {self.user.name} (ID: {self.user.id}) at {datetime.now()}')
        else:
            log.warning(f"Logged in as {self.user.name} (ID: {self.user.id}) but Warning: Guild with ID {config.DISCORD_GUILD_ID} not found")
    
    async def process_application_commands(*args):
        pass

    async def get_avatar_url(self, cache: Redis, user_id: int) -> str:
        cache_key = f'discord_avatar:{user_id}'
        
        cached_data = await cache.get(cache_key)
        current_time = time.time()

        if cached_data:
            data = json.loads(cached_data)
            last_updated = data['last_updated']
            
            await cache.expire(cache_key, self.AVATAR_CACHE_TTL)
            
            if current_time - last_updated < self.AVATAR_UPDATE_INTERVAL:
                return data['url']

        try:
            member = self.guild.get_member(user_id)
            if member:
                avatar_url = str(member.display_avatar.url)
            else:
                user = await self.fetch_user(user_id)
                avatar_url = str(user.avatar.url)

            cache_data = json.dumps({
                'url': avatar_url,
                'last_updated': current_time
            })
            await cache.setex(cache_key, self.AVATAR_CACHE_TTL, cache_data)

            return avatar_url
        except nextcord.errors.NotFound:
            log.warning(f"User with ID {user_id} not found")
            return config.DISCORD_DEFAULT_PFP
        except Exception as e:
            log.error(f"Error fetching avatar for user {user_id}: {e}")
            return config.DISCORD_DEFAULT_PFP


client = DiscordClient(
    intents=nextcord.Intents.all(), 
    rollout_update_known=False, 
    rollout_register_new=False, 
    rollout_delete_unknown=False, 
    rollout_associate_known=False, 
    lazy_load_commands=False
)

async def init_discord():
    await client.login(config.DISCORD_BOT_TOKEN)
    client.loop.create_task(client.connect())

def get_client():
    return client