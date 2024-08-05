from flask import jsonify, redirect, url_for, render_template_string
from ..models import Platform, UserPlatformMappings, BotSettings
from ..utils.discord_utils import add_discord_role
from ..utils.logger import log
from steam.steamid import SteamID
from datetime import datetime, timezone

def handle_auth(app, platform, token):
    if platform not in Platform._value2member_map_:
        log.info(f"platform {platform} is invalid")
        return jsonify({'error': 'Invalid platform'}), 400

    token_data = app.redis_db.hgetall(token)
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

def handle_verify(app, request):
    token = request.args.get('token')
    if token is None:
        log.info(f"Incorrect header token")
        return redirect(url_for('verified', failed=True, error="Incorrect header"))

    token_data = app.redis_db.hgetall(token)

    if not token_data:
        log.info("Token data is missing or invalid")
        return redirect(url_for('verified', failed=True))

    guild_id = token_data['guild_id']
    discord_uuid = token_data['discord_uuid']
    platform = token_data['platform']
    app.redis_db.delete(token)
    
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
        
        existing_mapping = app.session.query(UserPlatformMappings).filter_by(platform_id=user_id_str).first()
        log.info(f"Existing mapping from database: {existing_mapping}")
        if existing_mapping:
            if existing_mapping.user_id == int(discord_uuid):
                log.info(f"User {discord_uuid} has already verified with platform ID {user_id_str}")
                return redirect(url_for('verified', already_verified=True, steam_id=user_id_str, discord_uuid=discord_uuid))
            log.error(f"Platform ID {user_id_str} is already associated to a Discord account.")
            return redirect(url_for('verified', failed=True, error="Platform ID already associated to a Discord account"))
        
        mapping = app.session.query(UserPlatformMappings).filter_by(user_id=discord_uuid, platform=Platform(platform)).first()
        log.info(f"Mapping from database: {mapping}")
        
        if not mapping:
            new_mapping = UserPlatformMappings(guild_id=guild_id, user_id=discord_uuid, platform=Platform(platform), platform_id=user_id_str)
            app.session.add(new_mapping)
            app.session.commit()
            log.info(f"New mapping added: {new_mapping}")
        else:
            mapping.platform_id = user_id_str
            app.session.commit()
            log.info(f"Mapping updated: {mapping}")
        
        # Add the Discord role
        settings = app.session.query(BotSettings).where(BotSettings.guild_id == guild_id).first()
        if settings:
            role_id = settings.mm_verified_role
            if add_discord_role(guild_id, discord_uuid, role_id):
                log.info(f"Verified role added to user {discord_uuid} in guild {guild_id}")
            else:
                log.error(f"Failed to add verified role to user {discord_uuid} in guild {guild_id}")

    except Exception as e:
        app.session.rollback()
        log.error(f"Database error: {str(e)}")
        return redirect(url_for('verified', failed=True, error=str(e)))

    return redirect(url_for('verified', steam_id=user_id if platform == Platform.STEAM.value else None, discord_uuid=discord_uuid))

def handle_verified(request):
    steam_id = request.args.get('steam_id')
    discord_uuid = request.args.get('discord_uuid')
    failed = request.args.get('failed', False)
    error = request.args.get('error', None)
    already_verified = request.args.get('already_verified', False)

    with open("pages/authentication.html") as file:
        response_page = file.read()

    return render_template_string(response_page, steam_id=steam_id, discord_uuid=discord_uuid, failed=failed, error=error, already_verified=already_verified)