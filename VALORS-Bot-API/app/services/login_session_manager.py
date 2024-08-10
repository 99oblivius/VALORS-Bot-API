from uuid import uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.models import Session, User

class LoginSessionManager:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_session(self, user: User, ip_address: str, user_agent: str) -> Session:
        session = Session(
            user_id=user.id,
            session_token=str(uuid4()),
            ip_address=ip_address,
            user_agent=user_agent)
        self.db_session.add(session)
        await self.db_session.commit()
        return session

    async def get_session(self, session_token: str) -> Session:
        result = await self.db_session.execute(
            select(Session)
            .filter(Session.session_token == session_token))
        return result.scalars().first()

    async def update_session(self, session: Session):
        session.last_activity = datetime.now(timezone.utc)
        await self.db_session.commit()

    async def delete_user_sessions(self, session: Session):
        await self.db_session.delete(session)
        await self.db_session.commit()

    async def delete_session(self, session: Session):
        await self.db_session.delete(session)
        await self.db_session.commit()

    async def cleanup_old_sessions(self, max_age: timedelta = timedelta(days=30)):
        cutoff = datetime.now(timezone.utc) - max_age
        await self.db_session.execute(
            delete(Session)
            .where(Session.last_activity < cutoff))
        await self.db_session.commit()