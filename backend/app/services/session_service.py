from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.models.session import Session
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, data: SessionCreate) -> SessionResponse:
        session = Session(title=data.title)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return SessionResponse.model_validate(session)

    async def list_sessions(self) -> List[SessionResponse]:
        result = await self.db.execute(
            select(Session).order_by(Session.updated_at.desc())
        )
        sessions = result.scalars().all()
        return [SessionResponse.model_validate(s) for s in sessions]

    async def get_session(self, session_id: UUID) -> SessionResponse | None:
        result = await self.db.execute(
            select(Session)
            .options(selectinload(Session.messages))
            .where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()
        return SessionResponse.model_validate(session) if session else None

    async def update_session(self, session_id: UUID, data: SessionUpdate) -> SessionResponse:
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        session.title = data.title
        await self.db.commit()
        await self.db.refresh(session)
        return SessionResponse.model_validate(session)

    async def delete_session(self, session_id: UUID) -> None:
        await self.db.execute(delete(Session).where(Session.id == session_id))
        await self.db.commit()

    async def increment_message_count(self, session_id: UUID) -> None:
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if session:
            session.message_count += 1
            await self.db.commit()
