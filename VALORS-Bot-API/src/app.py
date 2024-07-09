from flask import Flask, request, jsonify, redirect, render_template_string, url_for
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, UniqueConstraint, Enum as sq_Enum
from sqlalchemy.orm import sessionmaker, declarative_base
from steam.steamid import SteamID
import os
import select
import hmac
import requests
from datetime import datetime, timezone
import redis
from dotenv import load_dotenv
from enum import Enum
import logging
from logger import Logger as log

# ENV KEYS:
#  SCHEMA_UPDATE_API_KEY
#  UPDATE_API_KEY
#  SECRET_KEY
#  
#  REDIS_HOST
#  REDIS_PORT
#  DATABASE_URL


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.logger.setLevel(logging.INFO)

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
DATABASE_URL = os.getenv('DATABASE_URL')

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_API_ENDPOINT = 'https://discord.com/api/v10'

redis_db = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

log.info(f"Server started at {datetime.now(timezone.utc)}")


class Platform(Enum):
    STEAM = "steam"
    PLAYSTATION = "playstation"


class UserPlatformMappings(Base):
    __tablename__ = 'user_platform_mappings'

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, nullable=True)
    user_id = Column(BigInteger, nullable=False)
    platform = Column(sq_Enum(Platform), nullable=False)
    platform_id = Column(String(64), unique=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('guild_id', 'user_id', 'platform', name='unique_guild_user_platform'),
    )


class BotSettings(Base):
    __tablename__ = 'bot_settings'

    guild_id           = Column(BigInteger, primary_key=True, nullable=False)
    mm_verified_role   = Column(BigInteger)


def add_discord_role(guild_id, user_id, role_id):
    url = f"{DISCORD_API_ENDPOINT}/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
    headers = {
        'Authorization': f'Bot {DISCORD_BOT_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    response = requests.put(url, headers=headers)
    if response.status_code == 204:
        log.info(f"Role {role_id} added to user {user_id} in guild {guild_id}")
        return True
    else:
        log.error(f"Failed to add role {role_id} to user {user_id} in guild {guild_id}. Status code: {response.status_code}, Response: {response.text}")
        return False

def write_to_pipe_with_timeout(pipe_path, message, timeout=5):
    try:
        pipe_fd = os.open(pipe_path, os.O_WRONLY | os.O_NONBLOCK)
        _, ready_to_write, _ = select.select([], [pipe_fd], [], timeout)
        if ready_to_write:
            os.write(pipe_fd, message.encode())
            os.close(pipe_fd)
            return True
        else:
            os.close(pipe_fd)
            return False
    except OSError as e:
        log.error(f"Error writing to pipe: {str(e)}")
        return False

@app.route('/update', methods=['POST'])
def update():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing Authorization header'}), 401
    
    update_type = request.args.get('type', None)
    
    if update_type == 'regular':
        if not hmac.compare_digest(auth_header, os.getenv('UPDATE_API_KEY', '')):
            log.error(f"UPDATE authentication failed")
            return jsonify({'error': 'Invalid token for regular update'}), 401
        
        try:
            if write_to_pipe_with_timeout('/hostpipe/apipipe', '/srv/ValorsLeague/VALORS-Bot-API/update.sh'):
                log.info("UPDATE called")
                return jsonify({'status': 'Update initiated successfully'}), 200
            else:
                log.error("UPDATE pipe write timed out")
                return jsonify({'error': 'Failed to write to pipe (timeout)'}), 500
        except IOError as e:
            log.error(f"UPDATE pipe failed")
            return jsonify({'error': 'Failed to write to pipe', 'details': str(e)}), 500
    
    else:
        log.error(f"/update invalid")
        return jsonify({'error': 'Invalid update type'}), 400

@app.route('/auth/<platform>/<token>')
def auth(platform, token):
    if platform not in Platform._value2member_map_:
        log.info(f"platform {platform} is invalid")
        return jsonify({'error': 'Invalid platform'}), 400

    token_data = redis_db.hgetall(token)
    if not token_data:
        log.info(f"token_data {token_data} is invalid")
        return jsonify({'error': 'Invalid token','reason': 'Your link is invalid or has expired. Generate a new link and try again.'}), 400
    
    expires_at = datetime.fromisoformat(token_data['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        log.info(f"token_data {token_data} expired")
        return jsonify({'error': 'Token expired','reason': 'Your link expired. Generate a new link and try again.'}), 400

    if platform == Platform.STEAM.value:
        steam_openid_url = 'https://steamcommunity.com/openid/login'
        params = {
            'openid.ns': 'http://specs.openid.net/auth/2.0',
            'openid.mode': 'checkid_setup',
            'openid.return_to': url_for('verify', _external=True, token=token),
            'openid.realm': url_for('verify', _external=True).rsplit('/', 1)[0] + '/',
            'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select'
        }
        auth_url = f"{steam_openid_url}?" + "&".join([f"{key}={value}" for key, value in params.items()])
        log.info(f"auth_url {auth_url} provided to token {token}")
        return redirect(auth_url)
    elif platform == Platform.PLAYSTATION.value:
        return jsonify({'error': 'PlayStation authentication not implemented yet'}), 501

@app.route('/verify')
def verify():
    token = request.args.get('token')
    if token is None:
        log.info(f"Incorrect header token")
        return redirect(url_for('verified', failed=True, error="Incorrect header"))

    token_data = redis_db.hgetall(token)

    if not token_data:
        log.info("Token data is missing or invalid")
        return redirect(url_for('verified', failed=True))

    guild_id = token_data['guild_id']
    discord_uuid = token_data['discord_uuid']
    platform = token_data['platform']
    redis_db.delete(token)
    
    log.info(f"Verification discord_uuid {discord_uuid} with token {token} for {platform}")
    if platform == Platform.STEAM.value:
        openid_claimed_id = request.args.get('openid.claimed_id')
        log.info(f"Received openid_claimed_id: {openid_claimed_id}")
        if not openid_claimed_id:
            log.error("openid_claimed_id is missing")
            return redirect(url_for('verified', failed=True))

        steamid = openid_claimed_id.split('/')[-1]
        user_id = SteamID(steamid).as_64
        log.info(f"Extracted steamid: {steamid}, user_id: {user_id}")
    elif platform == Platform.PLAYSTATION.value:
        user_id = "playstation_id_placeholder"
        log.info(f"Extracted user_id for PlayStation: {user_id}")

    try:
        user_id_str = str(user_id)
        
        existing_mapping = session.query(UserPlatformMappings).filter_by(platform_id=user_id_str).first()
        log.info(f"Existing mapping from database: {existing_mapping}")
        if existing_mapping:
            if existing_mapping.user_id == int(discord_uuid):
                log.info(f"User {discord_uuid} has already verified with platform ID {user_id_str}")
                return redirect(url_for('verified', already_verified=True, steam_id=user_id_str, discord_uuid=discord_uuid))
            log.error(f"Platform ID {user_id_str} is already associated to a Discord account.")
            return redirect(url_for('verified', failed=True, error="Platform ID already associated to a Discord account"))
        
        mapping = session.query(UserPlatformMappings).filter_by(user_id=discord_uuid, platform=Platform(platform)).first()
        log.info(f"Mapping from database: {mapping}")
        
        if not mapping:
            new_mapping = UserPlatformMappings(guild_id=guild_id, user_id=discord_uuid, platform=Platform(platform), platform_id=user_id_str)
            session.add(new_mapping)
            session.commit()
            log.info(f"New mapping added: {new_mapping}")
        else:
            mapping.platform_id = user_id_str
            session.commit()
            log.info(f"Mapping updated: {mapping}")
        
        # Add the Discord role
        settings = session.query(BotSettings).where(BotSettings.guild_id == guild_id).first()
        if settings:
            role_id = settings.mm_verified_role
            if add_discord_role(guild_id, discord_uuid, role_id):
                log.info(f"Verified role added to user {discord_uuid} in guild {guild_id}")
            else:
                log.error(f"Failed to add verified role to user {discord_uuid} in guild {guild_id}")

    except Exception as e:
        session.rollback()
        log.error(f"Database error: {str(e)}")
        return redirect(url_for('verified', failed=True, error=str(e)))
    finally:
        session.close()


    return redirect(url_for('verified', steam_id=user_id if platform == Platform.STEAM.value else None, discord_uuid=discord_uuid))

@app.route('/verified')
def verified():
    steam_id = request.args.get('steam_id')
    discord_uuid = request.args.get('discord_uuid')
    failed = request.args.get('failed', False)
    error = request.args.get('error', None)
    already_verified = request.args.get('already_verified', False)
    log.info(f"user_id {discord_uuid} landed on /verified with steam_id \"{steam_id}\" and error \"{error}\"")

    with open("pages/authentication.html") as file:
        response_page = file.read()

    return render_template_string(response_page, steam_id=steam_id, discord_uuid=discord_uuid, failed=failed, error=error, already_verified=already_verified)
