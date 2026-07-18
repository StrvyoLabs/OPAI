from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    # NullPool: on serverless (Vercel), a warm container can reuse this
    # module-level engine across invocations, but each invocation may run
    # on a *new* event loop -- and asyncpg connections are bound to the
    # loop they were created on. A pooled connection from a previous
    # invocation's loop is unusable on the next one and raises confusing
    # cross-loop errors. NullPool opens a fresh connection per checkout and
    # closes it after use, sidestepping that entirely (Supabase's own
    # PgBouncer pooler is doing the actual connection pooling anyway).
    poolclass=NullPool,
    # Supabase's connection pooler runs PgBouncer in transaction mode, which
    # doesn't support asyncpg's client-side prepared statement cache -- the
    # same statement name can collide across different pooled connections.
    connect_args={"statement_cache_size": 0},
)

async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
