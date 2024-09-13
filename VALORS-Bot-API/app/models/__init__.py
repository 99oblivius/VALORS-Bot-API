from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    BigInteger, 
    UniqueConstraint, 
    ForeignKey,
    DateTime,
    Boolean,
    TIMESTAMP,
    Float,
    ForeignKeyConstraint,
    MetaData,
    Enum as sq_Enum,
    Index
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from enum import Enum

Base = declarative_base()
metadata = MetaData()


class Platform(Enum):
    STEAM = "steam"
    PLAYSTATION = "playstation"

class MMBotUsers(Base):
    __tablename__ = 'mm_bot_users'

    guild_id      = Column(BigInteger, primary_key=True, nullable=False)
    user_id       = Column(BigInteger, primary_key=True, nullable=False)
    display_name  = Column(String(32))
    region        = Column(String(32))
    registered    = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(['guild_id', 'region'], ['bot_regions.guild_id', 'bot_regions.label']),
        {'extend_existing': True, 'autoload_with': None}
    )

    summary_stats = relationship("MMBotUserSummaryStats", uselist=False, back_populates="user")

class MMBotUserSummaryStats(Base):
    __tablename__ = 'mm_bot_user_summary_stats'

    guild_id        = Column(BigInteger, primary_key=True, nullable=False)
    user_id         = Column(BigInteger, primary_key=True, nullable=False)
    mmr             = Column(Float, default=900)
    games           = Column(Integer, default=0)
    wins            = Column(Integer, default=0)
    losses          = Column(Integer, default=0)
    ct_starts       = Column(Integer, default=0)
    top_score       = Column(Integer, default=0)
    top_kills       = Column(Integer, default=0)
    top_assists     = Column(Integer, default=0)
    total_score     = Column(Integer, default=0)
    total_kills     = Column(Integer, default=0)
    total_deaths    = Column(Integer, default=0)
    total_assists   = Column(Integer, default=0)

    __table_args__ = (
        ForeignKeyConstraint(['guild_id', 'user_id'], ['mm_bot_users.guild_id', 'mm_bot_users.user_id']),
        {'extend_existing': True, 'autoload_with': None}
    )
    
    user = relationship("MMBotUsers", back_populates="summary_stats")

class MMBotRanks(Base):
    __tablename__ = 'mm_bot_ranks'

    id             = Column(Integer, primary_key=True)
    guild_id       = Column(BigInteger, ForeignKey('bot_settings.guild_id'), nullable=False)
    mmr_threshold  = Column(Integer, nullable=False)
    role_id        = Column(BigInteger, nullable=False)
    timestamp      = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        {'extend_existing': True, 'autoload_with': None}
    )

class UserPlatformMappings(Base):
    __tablename__ = 'user_platform_mappings'
    __table_args__ = {'extend_existing': True, 'autoload_with': None}

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    platform = Column(sq_Enum(Platform))
    platform_id = Column(String(64))

    __table_args__ = (
        UniqueConstraint('guild_id', 'user_id', 'platform', name='unique_guild_user_platform'),
    )

class BotSettings(Base):
    __tablename__ = 'bot_settings'
    __table_args__ = {'extend_existing': True, 'autoload_with': None}

    guild_id = Column(BigInteger, primary_key=True)
    mm_verified_role = Column(BigInteger)


########################
# Valors League tables #
########################

class Roles(Enum):
    ADMIN  = "administrator"
    MOD    = "moderator"
    USER   = "user"

class Users(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'valors_league'}

    id = Column(Integer, primary_key=True)
    discord_id = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)

    roles = relationship("UserRoles", back_populates="user")
    sessions = relationship("Sessions", back_populates="user")

class UserRoles(Base):
    __tablename__ = 'user_roles'
    __table_args__ = {'schema': 'valors_league'}

    user_id = Column(Integer, ForeignKey('valors_league.users.id'), primary_key=True)
    role = Column(sq_Enum(Roles, name="roles", create_type=True), primary_key=True)

    user = relationship("Users", back_populates="roles")

class Teams(Base):
    __tablename__ = "teams"
    __table_args__ = {"schema": "valors_league"}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    bio = Column(String, nullable=True)
    color1 = Column(String, nullable=True)
    color2 = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    display_trophy = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    disbanded_at = Column(DateTime(timezone=True), nullable=True)

    users = relationship("TeamUsers", back_populates="team")

class TeamUsers(Base):
    __tablename__ = "team_users"
    __table_args__ = {"schema": "valors_league"}

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("valors_league.teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("valors_league.users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)

    team = relationship("Teams", back_populates="users")

class TeamCaptains(Base):
    __tablename__ = "team_captains"
    __table_args__ = {"schema": "valors_league"}

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("valors_league.teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("valors_league.users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True, default=None)

class TeamCoCaptains(Base):
    __tablename__ = "team_co_captains"
    __table_args__ = {"schema": "valors_league"}

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("valors_league.teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("valors_league.users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True, default=None)

class TeamJoinRequests(Base):
    __tablename__ = "team_join_requests"
    __table_args__ = {"schema": "valors_league"}

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("valors_league.teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("valors_league.users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    declined_at = Column(DateTime(timezone=True), nullable=True, default=None)
    accepted_at = Column(DateTime(timezone=True), nullable=True, default=None)

class Sessions(Base):
    __tablename__ = 'sessions'
    __table_args__ = {'schema': 'valors_league'}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('valors_league.users.id'))
    session_token = Column(String, unique=True, nullable=False)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    user = relationship("Users", back_populates="sessions")

async def init_db(app, database_url):
    engine = create_async_engine(database_url)
    app.state.engine = engine
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)
    app.state.AsyncSessionLocal = AsyncSessionLocal
    await init_models(engine)

async def init_models(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.reflect)
        await conn.run_sync(Base.metadata.create_all, tables=[table for table in Base.metadata.tables.values() if table.schema == 'valors_league'])