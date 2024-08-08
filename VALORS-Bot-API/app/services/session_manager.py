from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Session, User
import secrets
from datetime import datetime, timedelta

class AsyncSessionManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user: User, ip_address: str, user_agent: str) -> Session:
        session_token = secrets.token_urlsafe(32)
        new_session = Session(
            user_id=user.id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(new_session)
        await self.db.commit()
        return new_session

    async def get_session(self, session_token: str) -> Session | None:
        result = await self.db.execute(
            select(Session).filter(Session.session_token == session_token)
        )
        return result.scalar_one_or_none()

    async def update_session(self, session: Session):
        session.last_activity = datetime.utcnow()
        await self.db.commit()

    async def delete_session(self, session: Session):
        await self.db.delete(session)
        await self.db.commit()

    async def clear_expired_sessions(self, expiry_days: int = 30):
        expiry_date = datetime.utcnow() - timedelta(days=expiry_days)
        await self.db.execute(
            Session.__table__.delete().where(Session.last_activity < expiry_date)
        )
        await self.db.commit()