from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import desc, delete
from ..models import MMBotUserSummaryStats, MMBotRanks, Users, Roles
import logging

from ..models import *

async def get_db():
    async with AsyncSession() as session:
        try: yield session
        finally:
            await session.close()

async def get_user_from_discord(db: AsyncSession, discord_uid: int) -> Users:
    result = await db.execute(
        select(Users)
        .where(Users.discord_id == f'{discord_uid}'))
    return result.scalars().first()

async def upsert_user(db: AsyncSession, **user_info: dict) -> Users:
    result = await db.execute(
        select(Users)
        .filter(Users.discord_id == f"{user_info['discord_id']}"))
    user = result.scalars().first()

    if not user:
        user = Users(**user_info)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        await add_role(db, user.id, Roles.USER)

    return user

async def get_user(db: AsyncSession, user_id: int):
    query = select(Users).where(Users.id == user_id)
    result = await db.execute(query)
    return result.scalars().first()

async def add_role(db: AsyncSession, user_id: int, role: Roles):
    new_role = UserRoles(user_id=user_id, role=role)
    db.add(new_role)
    await db.commit()

async def remove_role(db: AsyncSession, user_id: int, role: Roles) -> bool:
    existing_role = await db.execute(
        select(UserRoles)
        .where(
            (UserRoles.user_id == user_id) & (UserRoles.role == role)))
    if not existing_role.scalar_one_or_none():
        return False
    
    await db.execute(
        delete(UserRoles)
        .where(
            UserRoles.user_id == user_id, 
            UserRoles.role == role))
    await db.commit()

async def get_user_roles(db: AsyncSession, user_id: int) -> List[Roles]:
    result = await db.execute(
        select(UserRoles.role)
        .where(UserRoles.user_id == user_id))
    return [role for (role,) in result.fetchall()]

async def get_user_from_session(db: AsyncSession, session_token: str) -> Optional[Users]:
    query = select(Session).options(joinedload(Session.user)).where(Session.session_token == session_token)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    return session.user if session else None

async def get_mm_ranks(db: AsyncSession, guild_id: int) -> List[MMBotRanks]:
    query = select(MMBotRanks).where(MMBotRanks.guild_id == guild_id).order_by(MMBotRanks.mmr_threshold)
    result = await db.execute(query)
    return result.scalars().all()

async def get_bot_settings(db: AsyncSession, guild_id: int) -> BotSettings:
    query = select(BotSettings).where(BotSettings.guild_id == guild_id)
    result = await db.execute(query)
    return result.scalars().first()

async def get_existing_mapping(db: AsyncSession, user_id_str: str) -> UserPlatformMappings:
    query = select(UserPlatformMappings).filter_by(platform_id=user_id_str)
    result = await db.execute(query)
    return result.scalars().first()

async def get_user_platform_mapping(db: AsyncSession, discord_uuid: str, platform: Platform) -> UserPlatformMappings:
    query = (
        select(UserPlatformMappings)
        .filter_by(user_id=int(discord_uuid), platform=platform))
    result = await db.execute(query)
    return result.scalars().first()

async def update_user_platform_mapping(db: AsyncSession, mapping: UserPlatformMappings, guild_id: int, discord_uuid: str, platform: Platform, user_id_str: str) -> UserPlatformMappings:
    log = logging.getLogger(__name__)

    if not mapping:
        new_mapping = UserPlatformMappings(
            guild_id=guild_id, 
            user_id=int(discord_uuid), 
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
            MMBotUserSummaryStats.guild_id == int(guild_id),
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