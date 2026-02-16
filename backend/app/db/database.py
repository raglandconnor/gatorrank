import ssl

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

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
    database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)

# create session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


# dependency to get db session


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
