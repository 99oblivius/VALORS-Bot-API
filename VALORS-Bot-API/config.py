import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    SECRET_KEY = os.getenv('SECRET_KEY')
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    DATABASE_URL = os.getenv('DATABASE_URL')
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    DISCORD_API_ENDPOINT = 'https://discord.com/api/v10'