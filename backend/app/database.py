from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.app_debug)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Import all models to ensure they are registered with Base
from app.models import session, message, knowledge, user, user_preference  # noqa: E402, F401


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # Rollback any pending transaction before closing
            # This prevents PendingRollbackError when reusing connections
            try:
                await session.rollback()
            except Exception:
                pass  # Ignore errors during rollback
            await session.close()
