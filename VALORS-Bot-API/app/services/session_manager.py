from uuid import uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session as DBSession
from app.models import Session, User

class SessionManager:
    def __init__(self, db_session: DBSession):
        self.db_session = db_session

    def create_session(self, user: User, ip_address: str, user_agent: str) -> Session:
        session = Session(
            user_id=user.id,
            session_token=str(uuid4()),
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db_session.add(session)
        self.db_session.commit()
        return session

    def get_session(self, session_token: str) -> Session:
        return self.db_session.query(Session).filter(Session.session_token == session_token).first()

    def update_session(self, session: Session):
        session.last_activity = datetime.now(timezone.utc)
        self.db_session.commit()

    def delete_session(self, session: Session):
        self.db_session.delete(session)
        self.db_session.commit()

    def cleanup_old_sessions(self, max_age: timedelta = timedelta(days=30)):
        cutoff = datetime.now(timezone.utc) - max_age
        self.db_session.query(Session).filter(Session.last_activity < cutoff).delete()
        self.db_session.commit()