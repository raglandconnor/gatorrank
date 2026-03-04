import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings

settings = get_settings()

connect_args: dict[str, object] = {
    "timeout": settings.DATABASE_CONNECT_TIMEOUT,
}

if settings.DATABASE_SSL:
    ssl_context = ssl.create_default_context()
    if not settings.DATABASE_SSL_VERIFY:
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

# create engine
engine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)

# create session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# dependency to get db session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
