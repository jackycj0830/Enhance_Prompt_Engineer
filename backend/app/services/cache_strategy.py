"""
多层缓存策略服务
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from enum import Enum

from app.core.cache import cache_manager, CacheManager
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheLevel(Enum):
    """缓存级别"""
    L1_MEMORY = "l1_memory"      # 内存缓存（最快）
    L2_REDIS = "l2_redis"        # Redis缓存（快）
    L3_DATABASE = "l3_database"  # 数据库缓存（慢）


class CacheStrategy(Enum):
    """缓存策略"""
    WRITE_THROUGH = "write_through"    # 写穿透
    WRITE_BACK = "write_back"          # 写回
    WRITE_AROUND = "write_around"      # 写绕过
    READ_THROUGH = "read_through"      # 读穿透
    CACHE_ASIDE = "cache_aside"        # 缓存旁路


class MultiLevelCache:
    """多层缓存管理器"""
    
    def __init__(self):
        self.cache_manager = cache_manager
        self.l1_cache: Dict[str, Dict] = {}  # 内存缓存
        self.max_l1_size = 1000
        self.default_ttl = {
            CacheLevel.L1_MEMORY: 300,    # 5分钟
            CacheLevel.L2_REDIS: 1800,    # 30分钟
            CacheLevel.L3_DATABASE: 3600  # 1小时
        }
        
    async def get(self, key: str, levels: List[CacheLevel] = None) -> Any:
        """多层缓存获取"""
        if levels is None:
            levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]
        
        for level in levels:
            try:
                value = await self._get_from_level(key, level)
                if value is not None:
                    # 回填到更高层缓存
                    await self._backfill_cache(key, value, level, levels)
                    return value
            except Exception as e:
                logger.error(f"Failed to get from {level.value}: {e}")
                continue
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                  levels: List[CacheLevel] = None, strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH):
        """多层缓存设置"""
        if levels is None:
            levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]
        
        if strategy == CacheStrategy.WRITE_THROUGH:
            # 写穿透：同时写入所有层
            for level in levels:
                level_ttl = ttl or self.default_ttl[level]
                await self._set_to_level(key, value, level_ttl, level)
                
        elif strategy == CacheStrategy.WRITE_BACK:
            # 写回：只写入最高层，延迟写入其他层
            if levels:
                highest_level = levels[0]
                level_ttl = ttl or self.default_ttl[highest_level]
                await self._set_to_level(key, value, level_ttl, highest_level)
                
                # 异步写入其他层
                if len(levels) > 1:
                    asyncio.create_task(self._delayed_write(key, value, ttl, levels[1:]))
                    
        elif strategy == CacheStrategy.WRITE_AROUND:
            # 写绕过：跳过缓存，直接写入数据源
            # 这里只是示例，实际需要根据业务逻辑实现
            pass
    
    async def _get_from_level(self, key: str, level: CacheLevel) -> Any:
        """从指定层获取缓存"""
        if level == CacheLevel.L1_MEMORY:
            return self._get_l1_cache(key)
        elif level == CacheLevel.L2_REDIS:
            return await self.cache_manager.get(key)
        else:
            return None
    
    async def _set_to_level(self, key: str, value: Any, ttl: int, level: CacheLevel):
        """设置到指定层缓存"""
        if level == CacheLevel.L1_MEMORY:
            self._set_l1_cache(key, value, ttl)
        elif level == CacheLevel.L2_REDIS:
            await self.cache_manager.set(key, value, ttl)
    
    def _get_l1_cache(self, key: str) -> Any:
        """获取L1内存缓存"""
        if key in self.l1_cache:
            cache_item = self.l1_cache[key]
            if cache_item['expires_at'] > datetime.utcnow():
                return cache_item['value']
            else:
                del self.l1_cache[key]
        return None
    
    def _set_l1_cache(self, key: str, value: Any, ttl: int):
        """设置L1内存缓存"""
        # 清理过期缓存
        self._cleanup_l1_cache()
        
        # 限制缓存大小
        if len(self.l1_cache) >= self.max_l1_size:
            oldest_key = min(self.l1_cache.keys(), 
                           key=lambda k: self.l1_cache[k]['created_at'])
            del self.l1_cache[oldest_key]
        
        self.l1_cache[key] = {
            'value': value,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(seconds=ttl)
        }
    
    def _cleanup_l1_cache(self):
        """清理过期的L1缓存"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, item in self.l1_cache.items()
            if item['expires_at'] <= now
        ]
        for key in expired_keys:
            del self.l1_cache[key]
    
    async def _backfill_cache(self, key: str, value: Any, found_level: CacheLevel, 
                            all_levels: List[CacheLevel]):
        """回填缓存到更高层"""
        found_index = all_levels.index(found_level)
        
        # 回填到更高层缓存
        for i in range(found_index):
            level = all_levels[i]
            ttl = self.default_ttl[level]
            await self._set_to_level(key, value, ttl, level)
    
    async def _delayed_write(self, key: str, value: Any, ttl: Optional[int], 
                           levels: List[CacheLevel]):
        """延迟写入其他层缓存"""
        await asyncio.sleep(0.1)  # 短暂延迟
        
        for level in levels:
            level_ttl = ttl or self.default_ttl[level]
            await self._set_to_level(key, value, level_ttl, level)
    
    async def invalidate(self, key: str, levels: List[CacheLevel] = None):
        """失效缓存"""
        if levels is None:
            levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]
        
        for level in levels:
            try:
                if level == CacheLevel.L1_MEMORY:
                    if key in self.l1_cache:
                        del self.l1_cache[key]
                elif level == CacheLevel.L2_REDIS:
                    await self.cache_manager.delete(key)
            except Exception as e:
                logger.error(f"Failed to invalidate {level.value}: {e}")


class SmartCacheManager:
    """智能缓存管理器"""
    
    def __init__(self):
        self.multi_cache = MultiLevelCache()
        self.access_patterns: Dict[str, Dict] = {}
        self.cache_stats: Dict[str, Dict] = {}
    
    async def get_with_analytics(self, key: str, data_loader: Callable = None) -> Any:
        """带分析的缓存获取"""
        start_time = datetime.utcnow()
        
        # 记录访问模式
        self._record_access(key)
        
        # 尝试从缓存获取
        value = await self.multi_cache.get(key)
        
        if value is not None:
            # 缓存命中
            self._record_cache_hit(key, start_time)
            return value
        
        # 缓存未命中，从数据源加载
        if data_loader:
            value = await data_loader()
            if value is not None:
                # 根据访问模式选择缓存策略
                strategy = self._choose_cache_strategy(key)
                levels = self._choose_cache_levels(key)
                ttl = self._calculate_ttl(key)
                
                await self.multi_cache.set(key, value, ttl, levels, strategy)
            
            self._record_cache_miss(key, start_time)
            return value
        
        return None
    
    def _record_access(self, key: str):
        """记录访问模式"""
        if key not in self.access_patterns:
            self.access_patterns[key] = {
                'count': 0,
                'last_access': None,
                'access_times': []
            }
        
        now = datetime.utcnow()
        pattern = self.access_patterns[key]
        pattern['count'] += 1
        pattern['last_access'] = now
        pattern['access_times'].append(now)
        
        # 只保留最近100次访问记录
        if len(pattern['access_times']) > 100:
            pattern['access_times'] = pattern['access_times'][-100:]
    
    def _record_cache_hit(self, key: str, start_time: datetime):
        """记录缓存命中"""
        if key not in self.cache_stats:
            self.cache_stats[key] = {'hits': 0, 'misses': 0, 'avg_response_time': 0}
        
        self.cache_stats[key]['hits'] += 1
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # 更新平均响应时间
        stats = self.cache_stats[key]
        total_requests = stats['hits'] + stats['misses']
        stats['avg_response_time'] = (
            (stats['avg_response_time'] * (total_requests - 1) + response_time) / total_requests
        )
    
    def _record_cache_miss(self, key: str, start_time: datetime):
        """记录缓存未命中"""
        if key not in self.cache_stats:
            self.cache_stats[key] = {'hits': 0, 'misses': 0, 'avg_response_time': 0}
        
        self.cache_stats[key]['misses'] += 1
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # 更新平均响应时间
        stats = self.cache_stats[key]
        total_requests = stats['hits'] + stats['misses']
        stats['avg_response_time'] = (
            (stats['avg_response_time'] * (total_requests - 1) + response_time) / total_requests
        )
    
    def _choose_cache_strategy(self, key: str) -> CacheStrategy:
        """选择缓存策略"""
        pattern = self.access_patterns.get(key, {})
        access_count = pattern.get('count', 0)
        
        # 根据访问频率选择策略
        if access_count > 100:
            return CacheStrategy.WRITE_THROUGH  # 高频访问使用写穿透
        elif access_count > 10:
            return CacheStrategy.WRITE_BACK     # 中频访问使用写回
        else:
            return CacheStrategy.CACHE_ASIDE    # 低频访问使用缓存旁路
    
    def _choose_cache_levels(self, key: str) -> List[CacheLevel]:
        """选择缓存层级"""
        pattern = self.access_patterns.get(key, {})
        access_count = pattern.get('count', 0)
        
        # 根据访问频率选择缓存层级
        if access_count > 50:
            return [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]  # 高频使用多层缓存
        elif access_count > 10:
            return [CacheLevel.L2_REDIS]  # 中频使用Redis缓存
        else:
            return [CacheLevel.L2_REDIS]  # 低频也使用Redis缓存
    
    def _calculate_ttl(self, key: str) -> int:
        """计算TTL"""
        pattern = self.access_patterns.get(key, {})
        access_times = pattern.get('access_times', [])
        
        if len(access_times) < 2:
            return 1800  # 默认30分钟
        
        # 计算访问间隔
        intervals = []
        for i in range(1, len(access_times)):
            interval = (access_times[i] - access_times[i-1]).total_seconds()
            intervals.append(interval)
        
        # 基于平均访问间隔计算TTL
        avg_interval = sum(intervals) / len(intervals)
        
        if avg_interval < 60:      # 1分钟内
            return 300             # 5分钟TTL
        elif avg_interval < 300:   # 5分钟内
            return 900             # 15分钟TTL
        elif avg_interval < 1800:  # 30分钟内
            return 3600            # 1小时TTL
        else:
            return 7200            # 2小时TTL
    
    async def get_cache_analytics(self) -> Dict:
        """获取缓存分析数据"""
        analytics = {
            "total_keys": len(self.cache_stats),
            "hit_rate": 0,
            "miss_rate": 0,
            "avg_response_time": 0,
            "top_accessed_keys": [],
            "cache_efficiency": {}
        }
        
        if not self.cache_stats:
            return analytics
        
        total_hits = sum(stats['hits'] for stats in self.cache_stats.values())
        total_misses = sum(stats['misses'] for stats in self.cache_stats.values())
        total_requests = total_hits + total_misses
        
        if total_requests > 0:
            analytics["hit_rate"] = (total_hits / total_requests) * 100
            analytics["miss_rate"] = (total_misses / total_requests) * 100
        
        # 计算平均响应时间
        response_times = [stats['avg_response_time'] for stats in self.cache_stats.values()]
        if response_times:
            analytics["avg_response_time"] = sum(response_times) / len(response_times)
        
        # 获取访问最多的键
        sorted_keys = sorted(
            self.access_patterns.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        analytics["top_accessed_keys"] = [
            {"key": key, "count": pattern['count']}
            for key, pattern in sorted_keys[:10]
        ]
        
        # 缓存效率分析
        for key, stats in self.cache_stats.items():
            total_key_requests = stats['hits'] + stats['misses']
            if total_key_requests > 0:
                hit_rate = (stats['hits'] / total_key_requests) * 100
                analytics["cache_efficiency"][key] = {
                    "hit_rate": hit_rate,
                    "total_requests": total_key_requests,
                    "avg_response_time": stats['avg_response_time']
                }
        
        return analytics


# 全局智能缓存管理器实例
smart_cache = SmartCacheManager()
