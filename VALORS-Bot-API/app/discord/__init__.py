import nextcord
from datetime import datetime
from config import config
from ..utils.logger import log

class DiscordClient(nextcord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.guild = None

    async def on_ready(self):
        self.guild = self.get_guild(config.DISCORD_GUILD_ID)
        if self.guild:
            log.info(f'Logged in as {self.user.name} (ID: {self.user.id}) at {datetime.now()}')
        else:
            log.warning(f"Warning: Guild with ID {config.DISCORD_GUILD_ID} not found")
    
    async def process_application_commands(*args):
        pass

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