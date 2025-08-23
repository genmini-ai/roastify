import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
import hashlib

import redis
from config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(self):
        self.redis_client = None
        self.enabled = settings.cache_enabled
        
        if self.enabled and settings.redis_url:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_timeout=5.0
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis connection failed, disabling cache: {e}")
                self.enabled = False
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create cache key"""
        # Hash long identifiers
        if len(identifier) > 100:
            identifier = hashlib.md5(identifier.encode()).hexdigest()
        return f"roastify:{prefix}:{identifier}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get failed for {key}: {e}")
        
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire_seconds: int = 3600
    ) -> bool:
        """Set value in cache"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, expire_seconds, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set failed for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete from cache"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete failed for {key}: {e}")
            return False
    
    # Specific cache methods
    async def get_profile(self, url: str) -> Optional[dict]:
        """Get cached profile data"""
        key = self._make_key("profile", url)
        return await self.get(key)
    
    async def cache_profile(self, url: str, profile_data: dict) -> bool:
        """Cache profile data for 24 hours"""
        key = self._make_key("profile", url)
        return await self.set(key, profile_data, expire_seconds=86400)  # 24 hours
    
    async def get_analysis(self, profile_hash: str) -> Optional[dict]:
        """Get cached analysis"""
        key = self._make_key("analysis", profile_hash)
        return await self.get(key)
    
    async def cache_analysis(self, profile_hash: str, analysis: dict) -> bool:
        """Cache analysis for 12 hours"""
        key = self._make_key("analysis", profile_hash)
        return await self.set(key, analysis, expire_seconds=43200)  # 12 hours
    
    async def get_lyrics(self, analysis_hash: str, style: str) -> Optional[dict]:
        """Get cached lyrics"""
        key = self._make_key("lyrics", f"{analysis_hash}:{style}")
        return await self.get(key)
    
    async def cache_lyrics(self, analysis_hash: str, style: str, lyrics: dict) -> bool:
        """Cache lyrics for 6 hours"""
        key = self._make_key("lyrics", f"{analysis_hash}:{style}")
        return await self.set(key, lyrics, expire_seconds=21600)  # 6 hours
    
    async def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get job status"""
        key = self._make_key("job", job_id)
        return await self.get(key)
    
    async def update_job_status(self, job_id: str, status: dict) -> bool:
        """Update job status"""
        key = self._make_key("job", job_id)
        return await self.set(key, status, expire_seconds=7200)  # 2 hours
    
    async def get_result(self, job_id: str) -> Optional[dict]:
        """Get final result"""
        key = self._make_key("result", job_id)
        return await self.get(key)
    
    async def cache_result(self, job_id: str, result: dict) -> bool:
        """Cache final result for 7 days"""
        key = self._make_key("result", job_id)
        return await self.set(key, result, expire_seconds=604800)  # 7 days
    
    def create_hash(self, data: Any) -> str:
        """Create hash for data"""
        if isinstance(data, dict):
            # Sort keys for consistent hashing
            sorted_data = json.dumps(data, sort_keys=True)
        else:
            sorted_data = str(data)
        
        return hashlib.sha256(sorted_data.encode()).hexdigest()[:16]


# Global cache instance
cache = CacheManager()


async def get_cache() -> CacheManager:
    """Dependency injection for cache"""
    return cache