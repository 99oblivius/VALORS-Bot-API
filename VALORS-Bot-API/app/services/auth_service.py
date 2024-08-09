from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from ..models import Platform
from ..utils.discord import add_discord_role
from ..utils.logger import log
from ..utils.database import get_bot_settings, update_user_platform_mapping, get_user_platform_mapping, get_existing_mapping
from urllib.parse import urlencode
from steam.steamid import SteamID
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

templates = Jinja2Templates(directory="pages")

async def handle_auth(request: Request, platform: str, token: str):
    if platform not in Platform._value2member_map_:
        log.info(f"platform {platform} is invalid")
        raise HTTPException(status_code=400, detail={"error": "Invalid platform"})

    token_data = await request.app.redis_db.hgetall(token)
    if not token_data:
        log.info(f"token_data {token_data} is invalid")
        raise HTTPException(status_code=400, detail={"error": "Invalid token", "message": "Your link is invalid or has expired. Generate a new link and try again."})
    
    expires_at = datetime.fromisoformat(token_data['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        log.info(f"token_data {token_data} expired")
        raise HTTPException(status_code=400, detail={"error": "Token expired", "message": "Your link expired. Generate a new link and try again."})

    if platform == Platform.STEAM.value:
        steam_openid_url = 'https://steamcommunity.com/openid/login'
        return_to = request.url_for('verify')
        return_to = str(return_to.include_query_params(token=token))
        
        params = {
            'openid.ns': 'http://specs.openid.net/auth/2.0',
            'openid.mode': 'checkid_setup',
            'openid.return_to': return_to,
            'openid.realm': str(request.base_url),
            'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select'
        }
        auth_url = f"{steam_openid_url}?{urlencode(params)}"
        log.info(f"auth_url {auth_url} provided to token {token}")
        return RedirectResponse(url=auth_url)
    elif platform == Platform.PLAYSTATION.value:
        raise HTTPException(status_code=501, detail={"error": 'PlayStation authentication not implemented yet'})

async def handle_verify(request: Request):
    token = request.query_params.get('token')
    if token is None:
        log.info(f"Incorrect header token")
        return RedirectResponse(url=str(request.url_for('verified').include_query_params(failed=True, error="Incorrect header")))

    token_data = await request.app.redis_db.hgetall(token)

    if not token_data:
        log.info("Token data is missing or invalid")
        return RedirectResponse(url=str(request.url_for('verified').include_query_params(failed=True)))

    guild_id = token_data['guild_id']
    discord_uuid = token_data['discord_uuid']
    platform = token_data['platform']
    await request.app.redis_db.delete(token)
    
    log.info(f"Verification discord_uuid {discord_uuid} with token {token} for {platform}")
    if platform == Platform.STEAM.value:
        openid_claimed_id = request.query_params.get('openid.claimed_id')
        log.info(f"Received openid_claimed_id: {openid_claimed_id}")
        if not openid_claimed_id:
            log.error("openid_claimed_id is missing")
            return RedirectResponse(url=str(request.url_for('verified').include_query_params(failed=True)))

        steamid = openid_claimed_id.split('/')[-1]
        user_id = SteamID(steamid).as_64
        log.info(f"Extracted steamid: {steamid}, user_id: {user_id}")
    elif platform == Platform.PLAYSTATION.value:
        user_id = "playstation_id_placeholder"
        log.info(f"Extracted user_id for PlayStation: {user_id}")

    db = request.state.db
    try:
        user_id_str = str(user_id)
        
        existing_mapping = await get_existing_mapping(db, user_id_str)
        if existing_mapping:
            if existing_mapping.user_id == int(discord_uuid):
                log.info(f"User {discord_uuid} has already verified with platform ID {user_id_str}")
                return RedirectResponse(url=str(request.url_for('verified').include_query_params(already_verified=True, steam_id=user_id_str, discord_uuid=discord_uuid)))
            log.error(f"Platform ID {user_id_str} is already associated to a Discord account.")
            return RedirectResponse(url=str(request.url_for('verified').include_query_params(failed=True, error="Platform ID already associated to a Discord account")))
        
        mapping = await get_user_platform_mapping(db, discord_uuid, Platform(platform))
        log.info(f"Mapping from database: {mapping}")
        
        await update_user_platform_mapping(
            db, mapping, 
            guild_id, 
            discord_uuid, 
            Platform(platform), 
            user_id_str)
        
        # Add the Discord role
        settings = await get_bot_settings(db, guild_id)
        if settings:
            role_id = settings.mm_verified_role
            if await add_discord_role(guild_id, discord_uuid, role_id):
                log.info(f"Verified role added to user {discord_uuid} in guild {guild_id}")
            else:
                log.error(f"Failed to add verified role to user {discord_uuid} in guild {guild_id}")

    except Exception as e:
        db.rollback()
        log.error(f"Database error: {str(e)}")
        return RedirectResponse(url=str(request.url_for('verified').include_query_params(failed=True, error=str(e))))

    return RedirectResponse(url=str(request.url_for('verified').include_query_params(steam_id=user_id if platform == Platform.STEAM.value else None, discord_uuid=discord_uuid)))


async def handle_verified(request: Request):
    steam_id = request.query_params.get('steam_id')
    discord_uuid = request.query_params.get('discord_uuid')
    failed = request.query_params.get('failed', False)
    error = request.query_params.get('error', None)
    already_verified = request.query_params.get('already_verified', False)

    return templates.TemplateResponse("authentication.html", {
        "request": request,
        "steam_id": steam_id,
        "discord_uuid": discord_uuid,
        "failed": failed,
        "error": error,
        "already_verified": already_verified
    })