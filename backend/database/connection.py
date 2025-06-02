"""
🗄️ Database Connection and Operations
Centralized database management with connection pooling and indexing
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Singleton database manager with connection pooling"""
    
    _instance: Optional['DatabaseManager'] = None
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self, mongo_url: str, db_name: Optional[str] = None):
        """Initialize database connection with optimized settings"""
        if self._client is None:
            try:
                # MongoDB connection with production optimizations
                self._client = AsyncIOMotorClient(
                    mongo_url,
                    maxPoolSize=50,  # Maximum connections in pool
                    minPoolSize=5,   # Minimum connections to maintain
                    maxIdleTimeMS=30000,  # Close connections after 30s idle
                    waitQueueTimeoutMS=5000,  # Wait up to 5s for connection
                    serverSelectionTimeoutMS=5000,  # Server selection timeout
                    connectTimeoutMS=5000,  # Connection timeout
                    socketTimeoutMS=30000,  # Socket timeout
                    retryWrites=True,  # Enable retryable writes
                    retryReads=True,   # Enable retryable reads
                )
                
                # Test connection
                await self._client.admin.command('ping')
                
                # Get database
                if db_name:
                    self._database = self._client[db_name]
                else:
                    self._database = self._client.get_database()
                
                logger.info("✅ Database connection established successfully")
                
            except Exception as e:
                logger.error(f"❌ Database connection failed: {e}")
                raise
    
    async def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("🔌 Database connection closed")
    
    @property
    def client(self) -> AsyncIOMotorClient:
        """Get database client"""
        if self._client is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._client
    
    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if self._database is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._database
    
    async def create_indexes(self):
        """Create all database indexes for optimal performance"""
        try:
            logger.info("🔧 Creating database indexes for optimal performance...")
            
            # Projects collection indexes
            await self._database.projects.create_index([("category", 1), ("risk_level", 1)], background=True)
            await self._database.projects.create_index([("status", 1), ("deadline", 1)], background=True)
            await self._database.projects.create_index([("id", 1)], unique=True, background=True)
            await self._database.projects.create_index([("status", 1)], background=True)
            await self._database.projects.create_index([("risk_level", 1)], background=True)
            await self._database.projects.create_index([("category", 1)], background=True)
            await self._database.projects.create_index([("deadline", 1)], background=True)
            await self._database.projects.create_index([("created_at", -1)], background=True)
            await self._database.projects.create_index([("updated_at", -1)], background=True)
            
            # Compound index for common dashboard queries
            await self._database.projects.create_index([
                ("status", 1), 
                ("category", 1), 
                ("risk_level", 1)
            ], background=True)
            
            # Index for AI analysis queries
            await self._database.projects.create_index([
                ("ai_analysis.success_probability", -1),
                ("status", 1)
            ], background=True)
            
            # Investments collection indexes
            await self._database.investments.create_index([("id", 1)], unique=True, background=True)
            await self._database.investments.create_index([("project_id", 1)], background=True)
            await self._database.investments.create_index([("investment_date", -1)], background=True)
            await self._database.investments.create_index([("created_at", -1)], background=True)
            
            # Compound index for investment analytics
            await self._database.investments.create_index([
                ("project_id", 1),
                ("investment_date", -1)
            ], background=True)
            
            # Alert settings collection indexes
            await self._database.alert_settings.create_index([("user_id", 1)], unique=True, background=True)
            
            # User authentication collection indexes
            await self._database.users.create_index([("id", 1)], unique=True, background=True)
            await self._database.users.create_index([("email", 1)], unique=True, background=True)
            await self._database.users.create_index([("username", 1)], unique=True, background=True)
            await self._database.users.create_index([("status", 1)], background=True)
            await self._database.users.create_index([("role", 1)], background=True)
            await self._database.users.create_index([("created_at", -1)], background=True)
            
            # User sessions collection indexes
            await self._database.user_sessions.create_index([("id", 1)], unique=True, background=True)
            await self._database.user_sessions.create_index([("user_id", 1)], background=True)
            await self._database.user_sessions.create_index([("refresh_token", 1)], unique=True, background=True)
            await self._database.user_sessions.create_index([("expires_at", 1)], background=True)
            await self._database.user_sessions.create_index([("is_active", 1)], background=True)
            
            # Email verification collection indexes
            await self._database.email_verifications.create_index([("id", 1)], unique=True, background=True)
            await self._database.email_verifications.create_index([("user_id", 1)], background=True)
            await self._database.email_verifications.create_index([("token", 1)], unique=True, background=True)
            await self._database.email_verifications.create_index([("expires_at", 1)], background=True)
            
            logger.info("✅ Database indexes created successfully!")
            
            # Log index information for monitoring
            projects_indexes = await self._database.projects.list_indexes().to_list(length=None)
            investments_indexes = await self._database.investments.list_indexes().to_list(length=None)
            users_indexes = await self._database.users.list_indexes().to_list(length=None)
            
            logger.info(f"📊 Projects collection has {len(projects_indexes)} indexes")
            logger.info(f"📊 Investments collection has {len(investments_indexes)} indexes")
            logger.info(f"📊 Users collection has {len(users_indexes)} indexes")
            
        except Exception as e:
            logger.error(f"❌ Failed to create database indexes: {e}")
            # Don't fail startup if indexes fail, just log the error
    
    async def health_check(self) -> dict:
        """Check database health and return statistics"""
        try:
            # Test basic connectivity
            await self._client.admin.command('ping')
            
            # Get collection statistics
            projects_count = await self._database.projects.count_documents({})
            investments_count = await self._database.investments.count_documents({})
            users_count = await self._database.users.count_documents({})
            
            return {
                "status": "healthy",
                "response_time_ms": 0,  # Could implement actual timing
                "collections": {
                    "projects_count": projects_count,
                    "investments_count": investments_count,
                    "users_count": users_count
                }
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for backward compatibility
async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db_manager.database

async def get_client() -> AsyncIOMotorClient:
    """Get database client"""
    return db_manager.client