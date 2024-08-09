from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc
from ..models import MMBotUserSummaryStats
import logging

from ..models import *

async def get_db():
    async with AsyncSession() as session:
        try: yield session
        finally:
            await session.close()

async def get_bot_settings(db: AsyncSession, guild_id: int):
    query = select(BotSettings).where(BotSettings.guild_id == guild_id)
    result = await db.execute(query)
    settings = result.scalars().first()
    return settings

async def get_existing_mapping(db: AsyncSession, user_id_str: str):
    query = select(UserPlatformMappings).filter_by(platform_id=user_id_str)
    result = await db.execute(query)
    existing_mapping = result.scalars().first()
    return existing_mapping

async def get_user_platform_mapping(db: AsyncSession, discord_uuid: str, platform: Platform):
    query = (
        select(UserPlatformMappings)
        .filter_by(user_id=discord_uuid, platform=platform)
        .options(selectinload(UserPlatformMappings.related_fields)))
    result = await db.execute(query)
    mapping = result.scalars().first()
    return mapping

async def update_user_platform_mapping(db: AsyncSession, mapping, guild_id: int, discord_uuid: str, platform: Platform, user_id_str: str):
    log = logging.getLogger(__name__)

    if not mapping:
        new_mapping = UserPlatformMappings(
            guild_id=guild_id, 
            user_id=discord_uuid, 
            platform=platform, 
            platform_id=user_id_str
        )
        db.add(new_mapping)
        await db.commit()
        await db.refresh(new_mapping)
        log.info(f"New mapping added: {new_mapping}")
        return new_mapping
    else:
        mapping.platform_id = user_id_str
        await db.commit()
        await db.refresh(mapping)
        log.info(f"Mapping updated: {mapping}")
        return mapping

async def get_match_making_leaderboard(db: AsyncSession, guild_id: int) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(MMBotUserSummaryStats)
        .where(
            MMBotUserSummaryStats.guild_id == guild_id,
            MMBotUserSummaryStats.games > 0)
        .order_by(desc(MMBotUserSummaryStats.mmr)))
    return [
        {
            "user_id": row.MMBotUserSummaryStats.user_id,
            "mmr": row.MMBotUserSummaryStats.mmr,
            "games": row.MMBotUserSummaryStats.games,
            "wins": row.MMBotUserSummaryStats.wins,
            "win_rate": row.MMBotUserSummaryStats.wins / row.MMBotUserSummaryStats.games if row.MMBotUserSummaryStats.games > 0 else 0,
            "avg_kills": row.MMBotUserSummaryStats.total_kills / row.MMBotUserSummaryStats.games if row.MMBotUserSummaryStats.games > 0 else 0,
            "avg_deaths": row.MMBotUserSummaryStats.total_deaths / row.MMBotUserSummaryStats.games if row.MMBotUserSummaryStats.games > 0 else 0,
            "avg_assists": row.MMBotUserSummaryStats.total_assists / row.MMBotUserSummaryStats.games if row.MMBotUserSummaryStats.games > 0 else 0,
            "avg_score": row.MMBotUserSummaryStats.total_score / row.MMBotUserSummaryStats.games if row.MMBotUserSummaryStats.games > 0 else 0,
        }
        for row in result
    ]