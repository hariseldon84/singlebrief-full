"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
import redis.asyncio as redis
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# SQLAlchemy base class
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.ENVIRONMENT == "development",
    future=True,
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
)

# Create async session factory
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Redis connection
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


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


async def get_redis() -> redis.Redis:
    """Get Redis connection"""
    return redis_client


async def init_db() -> None:
    """Initialize database"""
    try:
        # Test database connection
        async with engine.begin() as conn:
            # Import all models here to ensure they are registered
            from app.models import user, auth  # noqa
            
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