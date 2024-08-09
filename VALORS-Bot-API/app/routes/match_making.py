from typing import Dict, List
import asyncio

from fastapi import APIRouter, Request

from ..utils.database import get_match_making_leaderboard
from ..utils.discord import get_all_guild_members

router = APIRouter()

async def create_member_lookup(members: List[Dict]) -> Dict[str, str]:
    return {
        member['user']['id']: member['nick'] or member['user']['username']
        for member in members
    }

@router.get("/leaderboard")
async def leaderboard(request: Request):
    guild_id = 1217224187454685295
    members, leaderboard = await asyncio.gather(
        get_all_guild_members(guild_id),
        get_match_making_leaderboard(request.state.db, guild_id))
    member_lookup = await create_member_lookup(members)
    
    updated_leaderboard = []
    for entry in leaderboard:
        user_id = entry.pop('user_id', None)
        user_data = {}
        if user_id:
            username = member_lookup.get(f'{user_id}', f"({user_id})")
        # Sets 'username' at front of the dict
        user_data['username'] = username
        user_data.update(entry)
        updated_leaderboard.append(user_data)
    
    return updated_leaderboard