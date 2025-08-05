"""
性能监控中间件
"""

import time
import logging
import psutil
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.services.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)
settings = get_settings()


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.monitoring_service = MonitoringService()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并收集性能指标"""
        start_time = time.time()
        
        # 获取请求开始时的系统资源
        process = psutil.Process()
        start_memory = process.memory_info().rss
        start_cpu_percent = process.cpu_percent()
        
        # 处理请求
        response = await call_next(request)
        
        # 计算性能指标
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 毫秒
        
        end_memory = process.memory_info().rss
        memory_usage = end_memory - start_memory
        end_cpu_percent = process.cpu_percent()
        
        # 收集请求信息
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "user_agent": request.headers.get("user-agent", ""),
            "client_ip": self._get_client_ip(request),
            "response_time_ms": response_time,
            "status_code": response.status_code,
            "memory_usage_bytes": memory_usage,
            "cpu_percent": end_cpu_percent,
            "timestamp": start_time
        }
        
        # 记录性能日志
        self._log_performance(request_info)
        
        # 发送监控数据
        await self._send_monitoring_data(request_info)
        
        # 添加性能头信息
        response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
        response.headers["X-Memory-Usage"] = f"{memory_usage}B"
        
        # 检查性能阈值
        await self._check_performance_thresholds(request_info)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _log_performance(self, request_info: dict):
        """记录性能日志"""
        if request_info["response_time_ms"] > settings.SLOW_REQUEST_THRESHOLD:
            logger.warning(
                f"Slow request detected: {request_info['method']} {request_info['path']} "
                f"took {request_info['response_time_ms']:.2f}ms"
            )
        
        # 记录详细性能日志
        logger.info(
            f"Request: {request_info['method']} {request_info['path']} "
            f"Status: {request_info['status_code']} "
            f"Time: {request_info['response_time_ms']:.2f}ms "
            f"Memory: {request_info['memory_usage_bytes']}B"
        )
    
    async def _send_monitoring_data(self, request_info: dict):
        """发送监控数据"""
        try:
            await self.monitoring_service.record_request_metrics(request_info)
        except Exception as e:
            logger.error(f"Failed to send monitoring data: {e}")
    
    async def _check_performance_thresholds(self, request_info: dict):
        """检查性能阈值并触发告警"""
        # 响应时间阈值
        if request_info["response_time_ms"] > settings.CRITICAL_RESPONSE_TIME:
            await self.monitoring_service.trigger_alert(
                "critical_response_time",
                f"Critical response time: {request_info['response_time_ms']:.2f}ms for "
                f"{request_info['method']} {request_info['path']}"
            )
        
        # 内存使用阈值
        if request_info["memory_usage_bytes"] > settings.HIGH_MEMORY_THRESHOLD:
            await self.monitoring_service.trigger_alert(
                "high_memory_usage",
                f"High memory usage: {request_info['memory_usage_bytes']}B for "
                f"{request_info['method']} {request_info['path']}"
            )


class DatabasePerformanceMiddleware:
    """数据库性能监控中间件"""
    
    def __init__(self):
        self.monitoring_service = MonitoringService()
    
    async def __call__(self, query: str, parameters: dict, start_time: float, end_time: float):
        """记录数据库查询性能"""
        execution_time = (end_time - start_time) * 1000  # 毫秒
        
        query_info = {
            "query": query,
            "parameters": parameters,
            "execution_time_ms": execution_time,
            "timestamp": start_time
        }
        
        # 记录慢查询
        if execution_time > settings.SLOW_QUERY_THRESHOLD:
            logger.warning(
                f"Slow query detected: {execution_time:.2f}ms - {query[:100]}..."
            )
        
        # 发送监控数据
        try:
            await self.monitoring_service.record_database_metrics(query_info)
        except Exception as e:
            logger.error(f"Failed to record database metrics: {e}")


class MemoryProfiler:
    """内存分析器"""
    
    def __init__(self):
        self.snapshots = []
    
    def take_snapshot(self, label: str = ""):
        """获取内存快照"""
        import tracemalloc
        
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append({
            "label": label,
            "snapshot": snapshot,
            "timestamp": time.time()
        })
        
        return snapshot
    
    def compare_snapshots(self, snapshot1_idx: int = -2, snapshot2_idx: int = -1):
        """比较内存快照"""
        if len(self.snapshots) < 2:
            return None
        
        snapshot1 = self.snapshots[snapshot1_idx]["snapshot"]
        snapshot2 = self.snapshots[snapshot2_idx]["snapshot"]
        
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        memory_diff = []
        for stat in top_stats[:10]:  # 前10个最大差异
            memory_diff.append({
                "file": stat.traceback.format()[0],
                "size_diff": stat.size_diff,
                "count_diff": stat.count_diff
            })
        
        return memory_diff
    
    def get_top_memory_usage(self, snapshot_idx: int = -1):
        """获取内存使用排行"""
        if not self.snapshots:
            return []
        
        snapshot = self.snapshots[snapshot_idx]["snapshot"]
        top_stats = snapshot.statistics('lineno')
        
        memory_usage = []
        for stat in top_stats[:10]:
            memory_usage.append({
                "file": stat.traceback.format()[0],
                "size": stat.size,
                "count": stat.count
            })
        
        return memory_usage


class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self.profiles = []
    
    def start_profiling(self, label: str = ""):
        """开始性能分析"""
        import cProfile
        import pstats
        import io
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        return {
            "label": label,
            "profiler": profiler,
            "start_time": time.time()
        }
    
    def stop_profiling(self, profile_data: dict):
        """停止性能分析"""
        import pstats
        import io
        
        profiler = profile_data["profiler"]
        profiler.disable()
        
        # 生成统计信息
        stats_stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stats_stream)
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # 前20个函数
        
        profile_result = {
            "label": profile_data["label"],
            "duration": time.time() - profile_data["start_time"],
            "stats": stats_stream.getvalue(),
            "timestamp": time.time()
        }
        
        self.profiles.append(profile_result)
        return profile_result
    
    def get_hotspots(self, profile_idx: int = -1):
        """获取性能热点"""
        if not self.profiles:
            return []
        
        profile = self.profiles[profile_idx]
        lines = profile["stats"].split('\n')
        
        hotspots = []
        for line in lines[5:25]:  # 跳过头部，取前20行
            if line.strip() and not line.startswith('Ordered by'):
                parts = line.split()
                if len(parts) >= 6:
                    hotspots.append({
                        "calls": parts[0],
                        "total_time": parts[1],
                        "per_call": parts[2],
                        "cumulative": parts[3],
                        "per_call_cum": parts[4],
                        "function": ' '.join(parts[5:])
                    })
        
        return hotspots


# 全局实例
memory_profiler = MemoryProfiler()
performance_profiler = PerformanceProfiler()
db_performance_middleware = DatabasePerformanceMiddleware()
