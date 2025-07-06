"""
Base repository class for data access layer
"""

import logging
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """
    Base repository class providing common database operations
    """
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a raw SQL query
        """
        if not self.db_session:
            raise RuntimeError("Database session not available")
        
        try:
            result = await self.db_session.execute(query, params or {})
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch one row from query result
        """
        result = await self.execute_query(query, params)
        row = result.fetchone()
        return dict(row) if row else None
    
    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch all rows from query result
        """
        result = await self.execute_query(query, params)
        rows = result.fetchall()
        return [dict(row) for row in rows]
    
    async def execute_many(self, query: str, params_list: List[Dict[str, Any]]) -> None:
        """
        Execute query with multiple parameter sets
        """
        if not self.db_session:
            raise RuntimeError("Database session not available")
        
        try:
            for params in params_list:
                await self.db_session.execute(query, params)
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise
    
    async def begin_transaction(self):
        """
        Begin a database transaction
        """
        if not self.db_session:
            raise RuntimeError("Database session not available")
        
        return self.db_session.begin()
    
    async def commit_transaction(self):
        """
        Commit the current transaction
        """
        if not self.db_session:
            raise RuntimeError("Database session not available")
        
        await self.db_session.commit()
    
    async def rollback_transaction(self):
        """
        Rollback the current transaction
        """
        if not self.db_session:
            raise RuntimeError("Database session not available")
        
        await self.db_session.rollback()
    
    def build_where_clause(self, filters: Dict[str, Any], table_alias: str = "") -> tuple:
        """
        Build WHERE clause from filters
        """
        conditions = []
        params = {}
        
        prefix = f"{table_alias}." if table_alias else ""
        
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, list):
                    # IN clause
                    placeholders = ", ".join([f":filter_{key}_{i}" for i in range(len(value))])
                    conditions.append(f"{prefix}{key} IN ({placeholders})")
                    for i, val in enumerate(value):
                        params[f"filter_{key}_{i}"] = val
                elif isinstance(value, dict):
                    # Range or comparison operators
                    if "gte" in value:
                        conditions.append(f"{prefix}{key} >= :filter_{key}_gte")
                        params[f"filter_{key}_gte"] = value["gte"]
                    if "lte" in value:
                        conditions.append(f"{prefix}{key} <= :filter_{key}_lte")
                        params[f"filter_{key}_lte"] = value["lte"]
                    if "gt" in value:
                        conditions.append(f"{prefix}{key} > :filter_{key}_gt")
                        params[f"filter_{key}_gt"] = value["gt"]
                    if "lt" in value:
                        conditions.append(f"{prefix}{key} < :filter_{key}_lt")
                        params[f"filter_{key}_lt"] = value["lt"]
                    if "like" in value:
                        conditions.append(f"{prefix}{key} LIKE :filter_{key}_like")
                        params[f"filter_{key}_like"] = f"%{value['like']}%"
                else:
                    # Exact match
                    conditions.append(f"{prefix}{key} = :filter_{key}")
                    params[f"filter_{key}"] = value
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params
    
    def build_order_clause(self, sort_by: Optional[str], sort_order: str = "asc", table_alias: str = "") -> str:
        """
        Build ORDER BY clause
        """
        if not sort_by:
            return ""
        
        prefix = f"{table_alias}." if table_alias else ""
        direction = "DESC" if sort_order.lower() == "desc" else "ASC"
        
        return f"ORDER BY {prefix}{sort_by} {direction}"
    
    def build_limit_clause(self, limit: Optional[int], offset: int = 0) -> str:
        """
        Build LIMIT and OFFSET clause
        """
        if limit is None:
            return ""
        
        return f"LIMIT {limit} OFFSET {offset}"
    
    async def health_check(self) -> bool:
        """
        Check if repository/database is healthy
        """
        try:
            await self.execute_query("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Repository health check failed: {e}")
            return False
    
    def __enter__(self):
        """
        Context manager entry
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit
        """
        # Clean up resources if needed
        pass
    
    async def __aenter__(self):
        """
        Async context manager entry
        """
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit
        """
        # Clean up resources if needed
        pass
