from sqlalchemy import (
    create_engine, 
    Table,
    Column, 
    Integer, 
    String, 
    BigInteger, 
    UniqueConstraint, 
    ForeignKey,
    DateTime,
    Boolean,
    Enum as sq_Enum
)
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.sql import func
from enum import Enum
from config import config

def init_db(app):
    engine = create_engine(config.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    app.state.db = SessionLocal

Base = declarative_base()

#######################
# VALORS Match Making #
#######################
class Platform(Enum):
    STEAM = "steam"
    PLAYSTATION = "playstation"

class UserPlatformMappings(Base):
    __tablename__ = 'user_platform_mappings'

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, nullable=True)
    user_id = Column(BigInteger, nullable=False)
    platform = Column(sq_Enum(Platform), nullable=False)
    platform_id = Column(String(64), unique=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('guild_id', 'user_id', 'platform', name='unique_guild_user_platform'),
    )

class BotSettings(Base):
    __tablename__ = 'bot_settings'

    guild_id = Column(BigInteger, primary_key=True, nullable=False)
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