"""
Database configuration and session management
"""
import os
from typing import AsyncGenerator, Optional
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# Create the SQLAlchemy Base class
Base = declarative_base()

# Metadata for Alembic
metadata = MetaData()

# Database engines
engine: Optional[object] = None
async_engine: Optional[object] = None
SessionLocal: Optional[sessionmaker] = None
AsyncSessionLocal: Optional[async_sessionmaker] = None


def get_database_url() -> str:
    """Get database URL from environment or settings."""
    return os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")


def init_db() -> None:
    """Initialize database connections."""
    global engine, async_engine, SessionLocal, AsyncSessionLocal
    
    database_url = get_database_url()
    
    # Synchronous engine
    engine = create_engine(
        database_url,
        echo=settings.DB_ECHO,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    
    # Async engine for async operations
    async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    async_engine = create_async_engine(
        async_database_url,
        echo=settings.DB_ECHO,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    
    # Session makers
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def get_db() -> Session:
    """Get synchronous database session."""
    if not SessionLocal:
        init_db()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get asynchronous database session."""
    if not AsyncSessionLocal:
        init_db()
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def create_tables() -> None:
    """Create all database tables."""
    if not engine:
        init_db()
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """Drop all database tables."""
    if not engine:
        init_db()
    Base.metadata.drop_all(bind=engine)
