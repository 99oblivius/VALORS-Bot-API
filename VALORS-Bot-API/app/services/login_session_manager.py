from uuid import uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.models import Sessions, Users

class SessionManager:
    @staticmethod
    async def create(db_session: AsyncSession, user: Users, ip_address: str, user_agent: str) -> Sessions:
        session = Sessions(
            user_id=user.id,
            session_token=str(uuid4()),
            ip_address=ip_address,
            user_agent=user_agent)
        db_session.add(session)
        await db_session.commit()
        return session

    @staticmethod
    async def fetch(db_session: AsyncSession, session_token: str) -> Sessions:
        result = await db_session.execute(
            select(Sessions)
            .filter(Sessions.session_token == session_token))
        return result.scalars().first()

    @staticmethod
    async def update(db_session: AsyncSession, session: Sessions):
        session.last_activity = datetime.now(timezone.utc)
        await db_session.commit()

    @staticmethod
    async def delete(db_session: AsyncSession, session: Sessions):
        await db_session.delete(session)
        await db_session.commit()

    @staticmethod
    async def cleanup(db_session: AsyncSession, max_age: timedelta = timedelta(days=30)):
        cutoff = datetime.now(timezone.utc) - max_age
        await db_session.execute(
            delete(Sessions)
            .where(Sessions.last_activity < cutoff))
        await db_session.commit()