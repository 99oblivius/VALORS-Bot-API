import os
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = int(os.getenv('LOG_LEVEL', 2))
UPDATE_API_KEY = os.getenv('UPDATE_API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
DATABASE_URL = os.getenv('DATABASE_URL')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_API_ENDPOINT = 'https://discord.com/api/v10'