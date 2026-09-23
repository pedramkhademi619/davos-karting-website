from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from davos.platform.settings.app_settings import AppSettings


def create_engine(settings: AppSettings) -> AsyncEngine:
    """Pool sizing must respect replicas x (pool_size + max_overflow) <= PostgreSQL max_connections."""
    return create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
