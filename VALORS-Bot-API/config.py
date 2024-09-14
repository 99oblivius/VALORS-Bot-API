import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    LOG_LEVEL             = int(os.getenv('LOG_LEVEL', 2))
    UPDATE_API_KEY        = os.getenv('UPDATE_API_KEY')
    SECRET_KEY            = os.getenv('SECRET_KEY')
    REDIS_HOST            = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT            = int(os.getenv('REDIS_PORT', 6379))
    DATABASE_URL          = os.getenv('DATABASE_URL')
    API_TOKEN             = os.getenv('API_TOKEN')

    DISCORD_API_ENDPOINT  = os.getenv('DISCORD_API_ENDPOINT', 'https://discord.com/api/v10')
    DISCORD_GUILD_ID      = int(os.getenv('DISCORD_GUILD_ID'))
    DISCORD_REDIRECT_URI  = os.getenv('DISCORD_REDIRECT_URI')

    DISCORD_BOT_ID        = int(os.getenv('DISCORD_BOT_ID'))
    DISCORD_BOT_TOKEN     = os.getenv('DISCORD_BOT_TOKEN')

    DISCORD_CLIENT_ID     = int(os.getenv('DISCORD_CLIENT_ID'))
    DISCORD_CLIENT_TOKEN  = os.getenv('DISCORD_CLIENT_TOKEN')

    UPLOAD_DIR            = os.getenv('UPLOAD_DIR', '/cdn')
    CDN_BASE_URL          = os.getenv('CDN_BASE_URL', 'http://localhost')

    DISCORD_DEFAULT_PFP   = "https://discord.com/assets/6debd47ed13483642cf09e832ed0bc1b.png"

config = Config()