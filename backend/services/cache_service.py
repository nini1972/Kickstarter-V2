"""
🗄️ Cache Service
Redis-based caching service with intelligent management
"""

import logging
import json
import redis.asyncio as redis
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

from config.settings import redis_config

logger = logging.getLogger(__name__)

class CacheService:
    """Advanced Redis caching service with pattern management"""
    
    def __init__(self):
        self.redis_client = None
        self.default_ttl = redis_config.CACHE_TTL
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                redis_config.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                retry_on_error=[redis.ConnectionError, redis.TimeoutError],
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Cache service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Cache service initialization failed: {e}")
            self.redis_client = None
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("🔌 Cache service connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                self._stats["hits"] += 1
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                self._stats["misses"] += 1
                logger.debug(f"Cache MISS: {key}")
                return None
                
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=self._json_serializer)
            
            await self.redis_client.setex(key, ttl, serialized_value)
            self._stats["sets"] += 1
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            if result:
                self._stats["deletes"] += 1
                logger.debug(f"Cache DELETE: {key}")
            return bool(result)
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self._stats["deletes"] += deleted
                logger.info(f"Cache DELETE PATTERN: {pattern} ({deleted} keys)")
                return deleted
            return 0
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        
        try:
            return await self.redis_client.exists(key) == 1
        except Exception as e:
            logger.error(f"Cache exists check error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key"""
        if not self.redis_client:
            return False
        
        try:
            return await self.redis_client.expire(key, ttl) == 1
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL for key"""
        if not self.redis_client:
            return -1
        
        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric value"""
        if not self.redis_client:
            return None
        
        try:
            return await self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement numeric value"""
        if not self.redis_client:
            return None
        
        try:
            return await self.redis_client.decr(key, amount)
        except Exception as e:
            logger.error(f"Cache decrement error for key {key}: {e}")
            return None
    
    # High-level caching patterns
    
    async def cache_project(self, project_id: str, project_data: Dict, ttl: int = 3600):
        """Cache project data"""
        key = f"project:{project_id}"
        return await self.set(key, project_data, ttl)
    
    async def get_cached_project(self, project_id: str) -> Optional[Dict]:
        """Get cached project data"""
        key = f"project:{project_id}"
        return await self.get(key)
    
    async def invalidate_project(self, project_id: str):
        """Invalidate all project-related cache"""
        patterns = [
            f"project:{project_id}",
            f"ai_analysis:{project_id}:*",
            f"project_stats:{project_id}",
            f"recommendations:*"  # Invalidate recommendations as they might include this project
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"Invalidated {total_deleted} cache entries for project {project_id}")
        return total_deleted
    
    async def cache_user_session(self, session_id: str, session_data: Dict, ttl: int = 86400):
        """Cache user session data"""
        key = f"session:{session_id}"
        return await self.set(key, session_data, ttl)
    
    async def get_cached_session(self, session_id: str) -> Optional[Dict]:
        """Get cached session data"""
        key = f"session:{session_id}"
        return await self.get(key)
    
    async def invalidate_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user"""
        pattern = f"session:*"
        # Note: This is a simplified approach. In production, you might want to
        # store user_id in session keys for more efficient invalidation
        return await self.delete_pattern(pattern)
    
    async def cache_analytics(self, analytics_type: str, data: Dict, ttl: int = 1800):
        """Cache analytics data"""
        key = f"analytics:{analytics_type}:{datetime.utcnow().strftime('%Y%m%d%H')}"
        return await self.set(key, data, ttl)
    
    async def get_cached_analytics(self, analytics_type: str) -> Optional[Dict]:
        """Get cached analytics data"""
        key = f"analytics:{analytics_type}:{datetime.utcnow().strftime('%Y%m%d%H')}"
        return await self.get(key)
    
    async def cache_search_results(self, query_hash: str, results: List, ttl: int = 600):
        """Cache search results"""
        key = f"search:{query_hash}"
        return await self.set(key, results, ttl)
    
    async def get_cached_search(self, query_hash: str) -> Optional[List]:
        """Get cached search results"""
        key = f"search:{query_hash}"
        return await self.get(key)
    
    # Rate limiting support
    
    async def check_rate_limit(self, identifier: str, limit: int, window: int) -> Dict[str, Any]:
        """Check rate limit for identifier"""
        if not self.redis_client:
            return {"allowed": True, "remaining": limit, "reset_time": 0}
        
        try:
            key = f"rate_limit:{identifier}"
            current = await self.redis_client.get(key)
            
            if current is None:
                # First request
                await self.redis_client.setex(key, window, 1)
                return {
                    "allowed": True,
                    "remaining": limit - 1,
                    "reset_time": datetime.utcnow().timestamp() + window
                }
            else:
                current_count = int(current)
                if current_count >= limit:
                    ttl = await self.redis_client.ttl(key)
                    return {
                        "allowed": False,
                        "remaining": 0,
                        "reset_time": datetime.utcnow().timestamp() + ttl
                    }
                else:
                    await self.redis_client.incr(key)
                    ttl = await self.redis_client.ttl(key)
                    return {
                        "allowed": True,
                        "remaining": limit - current_count - 1,
                        "reset_time": datetime.utcnow().timestamp() + ttl
                    }
                    
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return {"allowed": True, "remaining": limit, "reset_time": 0}
    
    # Statistics and monitoring
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if not self.redis_client:
                return {"status": "disconnected", "stats": self._stats}
            
            info = await self.redis_client.info()
            keys_count = await self.redis_client.dbsize()
            
            return {
                "status": "connected",
                "total_keys": keys_count,
                "memory_used": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "local_stats": self._stats,
                "hit_rate": self._calculate_hit_rate()
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e), "stats": self._stats}
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        if total_requests == 0:
            return 0.0
        return (self._stats["hits"] / total_requests) * 100
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            if not self.redis_client:
                return {"status": "disconnected"}
            
            # Test basic operations
            test_key = "health_check_test"
            test_value = {"test": True, "timestamp": datetime.utcnow().isoformat()}
            
            # Test set
            await self.set(test_key, test_value, 10)
            
            # Test get
            retrieved = await self.get(test_key)
            
            # Test delete
            await self.delete(test_key)
            
            if retrieved and retrieved.get("test") is True:
                return {
                    "status": "healthy",
                    "operations": "all_working",
                    "stats": await self.get_stats()
                }
            else:
                return {
                    "status": "degraded",
                    "operations": "partial_failure"
                }
                
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global cache service instance
cache_service = CacheService()