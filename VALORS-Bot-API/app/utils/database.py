from typing import List, Dict, Any, Optional
from fastapi import UploadFile
import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, delete, desc, update, and_
from ..models import MMBotUserSummaryStats, MMBotRanks, Users, Roles
from config import config

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

        await add_user_role(db, user.id, Roles.USER)

    return user

async def get_user(db: AsyncSession, user_id: int):
    query = select(Users).where(Users.id == user_id)
    result = await db.execute(query)
    return result.scalars().first()

async def total_user_count(db: AsyncSession, search: Optional[str]=None) -> int:
    query = select(func.count(Users.id))
    if search:
        query = query.where(Users.username.ilike(f"%{search}%"))
    result = await db.execute(query)
    return result.scalar()

async def get_users(
    db: AsyncSession,
    search: str = "",
    last_username: str = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    query = (
        select(Users)
        .where(Users.is_active == True)
        .order_by(Users.username))

    if search:
        query = query.where(Users.username.ilike(f"%{search}%"))

    if last_username is not None:
        query = query.where(Users.username > last_username)

    query = query.limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "discord_id": user.discord_id,
            "username": user.username,
            "email": user.email,
        }
        for user in users
    ]

async def add_user_role(db: AsyncSession, user_id: int, role: Roles) -> bool:
    existing_role = await db.execute(
        select(UserRoles)
        .where(
            (UserRoles.user_id == user_id) & (UserRoles.role == role)))
    if existing_role.scalar_one_or_none():
        return False
    
    new_role = UserRoles(user_id=user_id, role=role)
    db.add(new_role)
    await db.commit()
    return True

async def remove_user_role(db: AsyncSession, user_id: int, role: Roles) -> bool:
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
    return True

async def get_user_roles(db: AsyncSession, user_id: int) -> List[Roles]:
    result = await db.execute(
        select(UserRoles.role)
        .where(UserRoles.user_id == user_id))
    return [role for (role,) in result.fetchall()]

async def get_users_roles(db: AsyncSession, user_ids: List[int]) -> Dict[int, List[str]]:
    result = await db.execute(
        select(UserRoles.user_id, UserRoles.role)
        .where(UserRoles.user_id.in_(user_ids)))
    
    user_roles = {}
    for user_id, role in result.fetchall():
        if user_id not in user_roles:
            user_roles[user_id] = []
        user_roles[user_id].append(role.value)
        user_roles[user_id].sort()
    
    return user_roles

async def get_user_from_session(db: AsyncSession, session_token: str) -> Optional[Users]:
    query = select(Sessions).options(joinedload(Sessions.user)).where(Sessions.session_token == session_token)
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
        return new_mapping
    else:
        mapping.platform_id = user_id_str
        await db.commit()
        await db.refresh(mapping)
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

async def get_team(db: AsyncSession, team_id: int) -> Optional[Teams]:
    query = select(Teams).where(Teams.id == team_id)
    result = await db.execute(query)
    return result.scalars().first()

async def update_team(
    db: AsyncSession, 
    team_id: int, 
    team_data: dict, 
    logo_file: UploadFile = None
) -> Optional[Dict[str, Any]]:
    if logo_file:
        file_extension = os.path.splitext(logo_file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        
        file_path = os.path.join(config.UPLOAD_DIR, unique_filename)
        with open(file_path, "wb") as buffer:
            content = await logo_file.read()
            buffer.write(content)
        
        team_data['logo_url'] = f"{config.CDN_BASE_URL}/{unique_filename}"

    query = (
        update(Teams)
        .where(Teams.id == team_id)
        .values(**team_data)
        .returning(Teams)
    )
    result = await db.execute(query)
    await db.commit()

    updated_team = result.fetchone()
    if updated_team:
        return {
            "id": updated_team.id,
            "name": updated_team.name,
            "bio": updated_team.bio,
            "color1": updated_team.color1,
            "color2": updated_team.color2,
            "logo_url": updated_team.logo_url,
            "display_trophy": updated_team.display_trophy,
            "created_at": updated_team.created_at,
            "disbanded_at": updated_team.disbanded_at
        }
    return None

async def fetch_teams(
    db: AsyncSession,
    search: str = "",
    last_team_name: str = None,
    limit: int = 20
) -> List[Teams]:
    query = select(Teams).order_by(Teams.name)

    if search:
        query = query.where(Teams.name.ilike(f"%{search}%"))

    if last_team_name is not None:
        query = query.where(Teams.name > last_team_name)

    query = query.limit(limit)

    result = await db.execute(query)
    return result.scalars().all()

async def total_team_count(db: AsyncSession, search: Optional[str] = None) -> int:
    query = select(func.count(Teams.id))
    if search:
        query = query.where(Teams.name.ilike(f"%{search}%"))
    result = await db.execute(query)
    return result.scalar()

async def get_team_members(db: AsyncSession, team_id: int) -> List[Dict[str, Any]]:
    query = (
        select(
            Users.id,
            Users.discord_id,
            Users.username,
            TeamUsers.timestamp.label('joined_at'))
        .join(TeamUsers, and_(
            Users.id == TeamUsers.user_id,
            TeamUsers.team_id == team_id,
            TeamUsers.left_at.is_(None)))
        .order_by(TeamUsers.timestamp))
    result = await db.execute(query)
    members = result.all()

    return [
        {
            "id": member.id,
            "discord_id": member.discord_id,
            "username": member.username,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None
        } for member in members
    ]

async def add_team_member(db: AsyncSession, team_id: int, user_id: int) -> bool:
    new_member = TeamUsers(team_id=team_id, user_id=user_id)
    db.add(new_member)
    try:
        await db.commit()
        return True
    except Exception:
        await db.rollback()
        return False

async def remove_team_member(db: AsyncSession, team_id: int, user_id: int) -> bool:
    query = update(TeamUsers).where(
        TeamUsers.team_id == team_id,
        TeamUsers.user_id == user_id,
        TeamUsers.left_at.is_(None)
    ).values(left_at=func.now())
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0

async def create_join_request(db: AsyncSession, team_id: int, user_id: int) -> Optional[TeamJoinRequests]:
    new_request = TeamJoinRequests(team_id=team_id, user_id=user_id)
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)
    return new_request

async def get_team_join_requests(db: AsyncSession, team_id: int) -> List[TeamJoinRequests]:
    query = select(TeamJoinRequests).where(
        TeamJoinRequests.team_id == team_id,
        TeamJoinRequests.accepted_at.is_(None),
        TeamJoinRequests.declined_at.is_(None))
    result = await db.execute(query)
    return result.scalars().all()

async def process_join_request(db: AsyncSession, request_id: int, accept: bool) -> Optional[TeamJoinRequests]:
    query = select(TeamJoinRequests).where(TeamJoinRequests.id == request_id)
    result = await db.execute(query)
    join_request = result.scalar_one_or_none()
    
    if join_request:
        if accept:
            join_request.accepted_at = func.now()
            await add_team_member(db, join_request.team_id, join_request.user_id)
        else:
            join_request.declined_at = func.now()
        
        await db.commit()
        await db.refresh(join_request)
    
    return join_request

async def is_team_captain(db: AsyncSession, team_id: int, user_id: int) -> bool:
    query = select(TeamCaptains).where(
        TeamCaptains.team_id == team_id,
        TeamCaptains.user_id == user_id,
        TeamCaptains.revoked_at.is_(None))
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None

async def is_team_co_captain(db: AsyncSession, team_id: int, user_id: int) -> bool:
    query = select(TeamCoCaptains).where(
        TeamCoCaptains.team_id == team_id,
        TeamCoCaptains.user_id == user_id,
        TeamCoCaptains.revoked_at.is_(None))
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None

