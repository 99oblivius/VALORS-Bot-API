from flask import Flask, request, jsonify, redirect, render_template_string, url_for, current_app
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, UniqueConstraint, Enum as sq_Enum
from sqlalchemy.orm import sessionmaker, declarative_base
import subprocess
from steam.steamid import SteamID
import os
import hmac
import requests
from datetime import datetime, timezone
import redis
from dotenv import load_dotenv
from enum import Enum
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.logger.setLevel(logging.INFO)

# Config variables
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
DATABASE_URL = os.getenv('DATABASE_URL')

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_API_ENDPOINT = 'https://discord.com/api/v10'

# Redis configuration
redis_db = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Database configuration
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# SQLAlchemy base model
Base = declarative_base()

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
        current_app.logger.info(f"Role {role_id} added to user {user_id} in guild {guild_id}")
        return True
    else:
        current_app.logger.error(f"Failed to add role. Status code: {response.status_code}, Response: {response.text}")
        return False

@app.route('/update', methods=['POST'])
def update():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing Authorization header'}), 401
    
    update_type = request.args.get('type', 'regular')
    
    if update_type == 'schema':
        if not hmac.compare_digest(auth_header, os.getenv('SCHEMA_UPDATE_API_KEY', '')):
            return jsonify({'error': 'Invalid token for schema update'}), 401
        
        try:
            result = subprocess.run(['/srv/ValorsLeague/botapi/schema-update.sh'], 
                                    check=True, capture_output=True, text=True)
            return jsonify({'status': 'Schema update process completed', 'output': result.stdout}), 200
        except subprocess.CalledProcessError as e:
            return jsonify({'error': 'Error during schema update process', 'details': e.stderr}), 500
    
    elif update_type == 'regular':
        if not hmac.compare_digest(auth_header, os.getenv('UPDATE_API_KEY', '')):
            return jsonify({'error': 'Invalid token for regular update'}), 401
        
        try:
            with open('/hostpipe/apipipe', 'w') as pipe:
                pipe.write('/srv/ValorsLeague/botapi/update.sh')
            return jsonify({'status': 'Update initiated successfully'}), 200
        except IOError as e:
            return jsonify({'error': 'Failed to write to pipe', 'details': str(e)}), 500
    
    else:
        return jsonify({'error': 'Invalid update type'}), 400

@app.route('/auth/<platform>/<token>')
def auth(platform, token):
    if platform not in Platform._value2member_map_:
        return jsonify({'error': 'Invalid platform'}), 400

    token_data = redis_db.hgetall(token)
    if not token_data:
        return jsonify({'error': 'Invalid token','reason': 'Your link is invalid or has expired. Generate a new link and try again.'}), 400
    
    expires_at = datetime.fromisoformat(token_data['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
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
        return redirect(auth_url)
    elif platform == Platform.PLAYSTATION.value:
        return jsonify({'error': 'PlayStation authentication not implemented yet'}), 501

@app.route('/verify')
def verify():
    token = request.args.get('token')
    if token is None:
        return redirect(url_for('verified', failed=True, error="Incorrect header"))

    app.logger.info(f"Received token: {token}")
    token_data = redis_db.hgetall(token)
    app.logger.info(f"Token data from Redis: {token_data}")

    if not token_data:
        app.logger.error("Token data is missing or invalid")
        return redirect(url_for('verified', failed=True))

    guild_id = token_data['guild_id']
    discord_uuid = token_data['discord_uuid']
    platform = token_data['platform']
    redis_db.delete(token)
    
    if platform == Platform.STEAM.value:
        openid_claimed_id = request.args.get('openid.claimed_id')
        app.logger.info(f"Received openid_claimed_id: {openid_claimed_id}")
        if not openid_claimed_id:
            app.logger.error("openid_claimed_id is missing")
            return redirect(url_for('verified', failed=True))

        steamid = openid_claimed_id.split('/')[-1]
        user_id = SteamID(steamid).as_64
        app.logger.info(f"Extracted steamid: {steamid}, user_id: {user_id}")
    elif platform == Platform.PLAYSTATION.value:
        user_id = "playstation_id_placeholder"
        app.logger.info(f"Extracted user_id for PlayStation: {user_id}")

    try:
        user_id_str = str(user_id)
        
        existing_mapping = session.query(UserPlatformMappings).filter_by(platform_id=user_id_str).first()
        app.logger.info(f"Existing mapping from database: {existing_mapping}")
        if existing_mapping:
            if existing_mapping.user_id == int(discord_uuid):
                app.logger.info(f"User {discord_uuid} has already verified with platform ID {user_id_str}")
                return redirect(url_for('verified', already_verified=True, steam_id=user_id_str, discord_uuid=discord_uuid))
            app.logger.error(f"Platform ID {user_id_str} is already associated to a Discord account.")
            return redirect(url_for('verified', failed=True, error="Platform ID already associated to a Discord account"))
        
        mapping = session.query(UserPlatformMappings).filter_by(user_id=discord_uuid, platform=Platform(platform)).first()
        app.logger.info(f"Mapping from database: {mapping}")
        
        if not mapping:
            new_mapping = UserPlatformMappings(guild_id=guild_id, user_id=discord_uuid, platform=Platform(platform), platform_id=user_id_str)
            session.add(new_mapping)
            session.commit()
            app.logger.info(f"New mapping added: {new_mapping}")
        else:
            mapping.platform_id = user_id_str
            session.commit()
            app.logger.info(f"Mapping updated: {mapping}")
        
        # Add the Discord role
        settings = session.query(BotSettings).where(BotSettings.guild_id == guild_id).first()
        if settings:
            role_id = settings.mm_verified_role
            if add_discord_role(guild_id, discord_uuid, role_id):
                app.logger.info(f"Verified role added to user {discord_uuid} in guild {guild_id}")
            else:
                app.logger.error(f"Failed to add verified role to user {discord_uuid} in guild {guild_id}")

    except Exception as e:
        session.rollback()
        app.logger.error(f"Database error: {str(e)}")
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

    with open("pages/authentication.html") as file:
        response_page = file.read()

    return render_template_string(response_page, steam_id=steam_id, discord_uuid=discord_uuid, failed=failed, error=error, already_verified=already_verified)
