# app/routes/discord.py
from fastapi import APIRouter, HTTPException, Request
from ..utils.database import get_mm_ranks
from ..discord import get_client
from ..utils.utils import resize_image_url
from config import config
import httpx

router = APIRouter()

@router.get("/commands")
async def get_commands(request: Request):
    headers = {
        'Authorization': f'Bot {config.DISCORD_BOT_TOKEN}', 
        'Content-Type': 'application/json'
    }
    all_commands = []
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{config.DISCORD_API_ENDPOINT}/applications/{config.DISCORD_BOT_ID}/commands", 
            headers=headers)
        all_commands.extend(r.json())
    
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{config.DISCORD_API_ENDPOINT}/applications/{config.DISCORD_BOT_ID}/guilds/{config.DISCORD_GUILD_ID}/commands", 
            headers=headers)
        all_commands.extend(r.json())
    return all_commands

@router.get("/members")
async def get_guild_members(request: Request):
    client = get_client()
    guild = client.guild
    
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    ranks = await get_mm_ranks(request.state.db, config.DISCORD_GUILD_ID)

    members = []
    for member in guild.members:
        rank = next((role for role in member.roles if role.id in (r.role_id for r in ranks)), None)
        members.append({
            "id": str(member.id),
            "username": member.name,
            "nick": member.nick,
            "name": member.display_name,
            "discriminator": member.discriminator,
            "avatar_url": resize_image_url(member.display_avatar.url, 64).replace('.png', '.webp'),
            "status": str(member.status),
            "roles": [role.name for role in member.roles[1:]],
            "mm_rank": {
                "name": rank.name, 
                "color": f'{rank.color}',
                "url": resize_image_url(rank.icon.url, 24)
             } if rank else None,
            "is_bot": member.bot
        })
    
    return {"members": members}