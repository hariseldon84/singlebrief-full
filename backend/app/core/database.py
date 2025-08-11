"""
Database configuration and session management
"""

import redis.asyncio as redis
import structlog
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = structlog.get_logger(__name__)

# SQLAlchemy base class
Base = declarative_base()

# Create async engine
database_url = settings.DATABASE_URL_COMPUTED.replace("postgresql://", "postgresql+asyncpg://")

# Add SSL configuration for cloud databases (like Neon)
connect_args = {}
if "neon.tech" in database_url or "amazonaws.com" in database_url:
    connect_args = {"ssl": "require"}

engine = create_async_engine(
    database_url,
    echo=settings.ENVIRONMENT == "development",
    future=True,
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
    connect_args=connect_args,
)

# Create async session factory
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Redis connection
redis_client = redis.from_url(settings.REDIS_URL_COMPUTED, decode_responses=True)

async def get_db_session() -> AsyncSession:
    """Get database session"""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Alias for compatibility
get_async_session = get_db_session
get_db = get_db_session

async def get_redis() -> redis.Redis:
    """Get Redis connection"""
    return redis_client

async def init_db() -> None:
    """Initialize database"""
    try:
        # Test database connection
        async with engine.begin() as conn:
            # Import all models here to ensure they are registered
            from app.models import auth, user  # noqa

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")

        # Test Redis connection
        await redis_client.ping()
        logger.info("Redis connection established")

    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise

async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
    await redis_client.close()
