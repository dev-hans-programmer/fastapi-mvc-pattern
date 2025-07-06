"""
Database configuration and session management
"""

import logging
from typing import Optional, AsyncGenerator
from sqlalchemy import create_engine, MetaData, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager
import asyncio
from functools import lru_cache

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Database metadata
metadata = MetaData()

# Base class for ORM models
Base = declarative_base(metadata=metadata)

# Database engines
engine: Optional[create_engine] = None
async_engine: Optional[create_async_engine] = None

# Session makers
SessionLocal: Optional[sessionmaker] = None
AsyncSessionLocal: Optional[async_sessionmaker] = None


def create_database_engine():
    """
    Create database engine based on configuration
    """
    global engine, async_engine, SessionLocal, AsyncSessionLocal
    
    database_url = settings.get_database_url()
    
    if not database_url:
        logger.warning("No database URL configured, database operations will be disabled")
        return
    
    try:
        # Create synchronous engine
        engine = create_engine(
            database_url,
            poolclass=pool.QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=settings.DEBUG,
        )
        
        # Create async engine
        async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        async_engine = create_async_engine(
            async_database_url,
            poolclass=pool.QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=settings.DEBUG,
        )
        
        # Create session makers
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )
        
        AsyncSessionLocal = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        
        logger.info("Database engines created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database engines: {e}")
        raise


def get_db() -> Session:
    """
    Get synchronous database session
    """
    if not SessionLocal:
        raise RuntimeError("Database not initialized")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get asynchronous database session
    """
    if not AsyncSessionLocal:
        raise RuntimeError("Async database not initialized")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions
    """
    if not AsyncSessionLocal:
        raise RuntimeError("Async database not initialized")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """
    Database management utility class
    """
    
    def __init__(self):
        self.engine = engine
        self.async_engine = async_engine
        self.session_local = SessionLocal
        self.async_session_local = AsyncSessionLocal
    
    async def create_tables(self):
        """
        Create all database tables
        """
        if not self.async_engine:
            logger.warning("No async engine available, skipping table creation")
            return
        
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    async def drop_tables(self):
        """
        Drop all database tables
        """
        if not self.async_engine:
            logger.warning("No async engine available, skipping table drop")
            return
        
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    async def check_connection(self) -> bool:
        """
        Check database connection
        """
        if not self.async_engine:
            return False
        
        try:
            async with self.async_engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    async def get_table_names(self) -> list:
        """
        Get list of all table names
        """
        if not self.async_engine:
            return []
        
        try:
            async with self.async_engine.begin() as conn:
                result = await conn.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get table names: {e}")
            return []
    
    def get_sync_session(self) -> Session:
        """
        Get synchronous database session
        """
        if not self.session_local:
            raise RuntimeError("Database not initialized")
        return self.session_local()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get asynchronous database session
        """
        if not self.async_session_local:
            raise RuntimeError("Async database not initialized")
        
        async with self.async_session_local() as session:
            try:
                yield session
            finally:
                await session.close()


# Initialize database manager
@lru_cache()
def get_database_manager() -> DatabaseManager:
    """
    Get cached database manager instance
    """
    return DatabaseManager()


# Initialize database on module import
try:
    create_database_engine()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
