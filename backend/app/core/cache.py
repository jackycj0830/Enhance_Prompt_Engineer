"""
缓存系统
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import asyncio
import logging

import redis.asyncio as redis
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, Dict] = {}
        self.max_local_cache_size = 1000
        
    async def init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True
            )
            # 测试连接
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def close_redis(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{prefix}:{':'.join(map(str, args))}"
        if kwargs:
            key_data += f":{json.dumps(kwargs, sort_keys=True)}"
        
        # 对长键进行哈希
        if len(key_data) > 250:
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_data
    
    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        try:
            # 先尝试Redis
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value is not None:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
            
            # 降级到本地缓存
            if key in self.local_cache:
                cache_item = self.local_cache[key]
                if cache_item['expires_at'] > datetime.utcnow():
                    return cache_item['value']
                else:
                    del self.local_cache[key]
            
            return default
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存值"""
        try:
            # 序列化值
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = str(value)
            
            # 尝试Redis
            if self.redis_client:
                await self.redis_client.setex(key, ttl, serialized_value)
                return True
            
            # 降级到本地缓存
            self._set_local_cache(key, value, ttl)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def _set_local_cache(self, key: str, value: Any, ttl: int):
        """设置本地缓存"""
        # 清理过期缓存
        self._cleanup_local_cache()
        
        # 限制缓存大小
        if len(self.local_cache) >= self.max_local_cache_size:
            # 删除最旧的缓存项
            oldest_key = min(self.local_cache.keys(), 
                           key=lambda k: self.local_cache[k]['created_at'])
            del self.local_cache[oldest_key]
        
        self.local_cache[key] = {
            'value': value,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(seconds=ttl)
        }
    
    def _cleanup_local_cache(self):
        """清理过期的本地缓存"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, item in self.local_cache.items()
            if item['expires_at'] <= now
        ]
        for key in expired_keys:
            del self.local_cache[key]
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            # 删除Redis缓存
            if self.redis_client:
                await self.redis_client.delete(key)
            
            # 删除本地缓存
            if key in self.local_cache:
                del self.local_cache[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            if self.redis_client:
                return await self.redis_client.exists(key) > 0
            
            if key in self.local_cache:
                cache_item = self.local_cache[key]
                if cache_item['expires_at'] > datetime.utcnow():
                    return True
                else:
                    del self.local_cache[key]
            
            return False
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        try:
            count = 0
            
            if self.redis_client:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    count = await self.redis_client.delete(*keys)
            
            # 清理本地缓存
            import fnmatch
            local_keys = [
                key for key in self.local_cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            for key in local_keys:
                del self.local_cache[key]
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        stats = {
            "local_cache_size": len(self.local_cache),
            "local_cache_max_size": self.max_local_cache_size,
            "redis_connected": self.redis_client is not None
        }
        
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                stats.update({
                    "redis_used_memory": info.get("used_memory_human", "N/A"),
                    "redis_connected_clients": info.get("connected_clients", 0),
                    "redis_total_commands_processed": info.get("total_commands_processed", 0)
                })
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")
        
        return stats


# 缓存装饰器
def cache_result(prefix: str, ttl: int = 3600, key_func=None):
    """缓存函数结果的装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


class QueryCache:
    """数据库查询缓存"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.default_ttl = 1800  # 30分钟
    
    async def get_or_set(self, query_key: str, query_func, ttl: Optional[int] = None):
        """获取或设置查询缓存"""
        ttl = ttl or self.default_ttl
        
        # 尝试从缓存获取
        cached_result = await self.cache_manager.get(query_key)
        if cached_result is not None:
            return cached_result
        
        # 执行查询并缓存
        result = await query_func()
        await self.cache_manager.set(query_key, result, ttl)
        
        return result
    
    async def invalidate_user_cache(self, user_id: int):
        """清除用户相关缓存"""
        patterns = [
            f"user:{user_id}:*",
            f"prompts:user:{user_id}:*",
            f"templates:user:{user_id}:*",
            f"analyses:user:{user_id}:*"
        ]
        
        for pattern in patterns:
            await self.cache_manager.clear_pattern(pattern)
    
    async def invalidate_prompt_cache(self, prompt_id: int):
        """清除提示词相关缓存"""
        patterns = [
            f"prompt:{prompt_id}:*",
            f"analyses:prompt:{prompt_id}:*"
        ]
        
        for pattern in patterns:
            await self.cache_manager.clear_pattern(pattern)
    
    async def invalidate_template_cache(self, template_id: int):
        """清除模板相关缓存"""
        patterns = [
            f"template:{template_id}:*",
            "templates:*"  # 清除模板列表缓存
        ]
        
        for pattern in patterns:
            await self.cache_manager.clear_pattern(pattern)


class RateLimiter:
    """基于Redis的限流器"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """检查是否允许请求"""
        try:
            if not self.cache_manager.redis_client:
                return True  # 降级处理，允许所有请求
            
            current_time = int(datetime.utcnow().timestamp())
            window_start = current_time - window
            
            # 使用Redis的有序集合实现滑动窗口限流
            pipe = self.cache_manager.redis_client.pipeline()
            
            # 删除窗口外的记录
            pipe.zremrangebyscore(key, 0, window_start)
            
            # 获取当前窗口内的请求数
            pipe.zcard(key)
            
            # 添加当前请求
            pipe.zadd(key, {str(current_time): current_time})
            
            # 设置过期时间
            pipe.expire(key, window)
            
            results = await pipe.execute()
            current_count = results[1]
            
            return current_count < limit
            
        except Exception as e:
            logger.error(f"Rate limiter error for key {key}: {e}")
            return True  # 降级处理


# 全局缓存管理器实例
cache_manager = CacheManager()
query_cache = QueryCache(cache_manager)
rate_limiter = RateLimiter(cache_manager)
