# app/routes/discord.py
from fastapi import APIRouter, HTTPException, Request, Query
from typing import List, Optional
from pydantic import BaseModel
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

class MemberRank(BaseModel):
    name: str
    color: str
    url: str

class Member(BaseModel):
    id: str
    username: str
    nick: Optional[str]
    name: str
    discriminator: str
    avatar_url: str
    status: str
    roles: List[str]
    mm_rank: Optional[MemberRank]
    is_bot: bool

class MembersResponse(BaseModel):
    members: List[Member]
    total_members: int

def process_member(member, ranks):
    rank = next((role for role in member.roles if role.id in (r.role_id for r in ranks)), None)
    return Member(
        id=str(member.id),
        username=member.name,
        nick=member.nick,
        name=member.display_name,
        discriminator=member.discriminator,
        avatar_url=resize_image_url(member.display_avatar.url, 64).replace('.png', '.webp'),
        status=str(member.status),
        roles=[role.name for role in member.roles[1:]],
        mm_rank=MemberRank(
            name=rank.name,
            color=f'{rank.color}',
            url=resize_image_url(rank.icon.url, 24)
        ) if rank else None,
        is_bot=member.bot
    )

@router.get("/members", response_model=MembersResponse)
async def get_guild_members(request: Request, 
    page: Optional[int] = Query(None, ge=1),
    limit: Optional[int] = Query(None, ge=-1)
):
    if page is not None and limit is None:
        raise HTTPException(status_code=400, detail="When 'page' is provided, 'limit' is required")

    client = get_client()
    guild = client.guild
    
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    ranks = await get_mm_ranks(request.state.db, config.DISCORD_GUILD_ID)
    
    all_members = guild.members
    total_members = len(all_members)
    
    if page is None and limit is None:
        paginated_members = [process_member(member, ranks) for member in all_members]
    else:
        page = page or 1
        limit = limit or -1
        start = (page - 1) * limit
        end = -1 if limit == -1 else (start + limit)
        paginated_members = [process_member(member, ranks) for member in all_members[start:end]]

    return MembersResponse(members=paginated_members, total_members=total_members)