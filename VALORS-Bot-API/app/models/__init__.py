from sqlalchemy import create_engine, Column, Integer, String, BigInteger, UniqueConstraint, Enum as sq_Enum
from sqlalchemy.orm import sessionmaker, declarative_base
from enum import Enum

Base = declarative_base()

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

def init_db(app):
    engine = create_engine(app.config['DATABASE_URL'])
    Base.metadata.create_all(engine)
    app.session = sessionmaker(bind=engine)()