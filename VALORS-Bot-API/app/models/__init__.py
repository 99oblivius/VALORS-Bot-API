from sqlalchemy import (
    Table,
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
    Enum as sq_Enum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from enum import Enum
from config import config

Base = declarative_base()
metadata = MetaData()

async def init_db(app):
    engine = create_async_engine(config.DATABASE_URL)
    app.state.engine = engine

    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)
    app.state.AsyncSessionLocal = AsyncSessionLocal

    async with engine.begin() as conn:
        await conn.run_sync(metadata.reflect, schema='public')

async def init_models(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.reflect)

#######################
# VALORS Match Making #
#######################
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

class UserPlatformMappings(Base):
    __tablename__ = 'user_platform_mappings'
    __table_args__ = {'extend_existing': True, 'autoload_with': None}

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    platform = Column(sq_Enum(Platform))
    platform_id = Column(String(64))

class BotSettings(Base):
    __tablename__ = 'bot_settings'
    __table_args__ = {'extend_existing': True, 'autoload_with': None}

    guild_id = Column(BigInteger, primary_key=True)
    mm_verified_role = Column(BigInteger)

#################
# VALORS LEAGUE #
#################
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('valors_league.users.id')),
    Column('role_id', Integer, ForeignKey('valors_league.roles.id')),
    schema='valors_league'
)

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'valors_league'}

    id = Column(Integer, primary_key=True)
    discord_id = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    sessions = relationship("Session", back_populates="user")

class Role(Base):
    __tablename__ = 'roles'
    __table_args__ = {'schema': 'valors_league'}

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)

    users = relationship("User", secondary=user_roles, back_populates="roles")

class Session(Base):
    __tablename__ = 'sessions'
    __table_args__ = {'schema': 'valors_league'}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('valors_league.users.id'))
    session_token = Column(String, unique=True, nullable=False)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="sessions")