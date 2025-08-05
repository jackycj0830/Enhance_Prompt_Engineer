"""
性能分析服务
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PerformanceService:
    """性能分析服务"""
    
    def __init__(self):
        self.metrics_cache = {}
        self.alert_thresholds = {
            "response_time": 1000,  # 1秒
            "memory_usage": 100 * 1024 * 1024,  # 100MB
            "cpu_usage": 80,  # 80%
            "database_query_time": 500,  # 500ms
            "error_rate": 5  # 5%
        }
    
    async def collect_system_metrics(self) -> Dict:
        """收集系统性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_usage = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            }
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_usage = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
            
            # 网络IO
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            # 进程信息
            process = psutil.Process()
            process_info = {
                "pid": process.pid,
                "memory_rss": process.memory_info().rss,
                "memory_vms": process.memory_info().vms,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            }
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": memory_usage,
                "disk": disk_usage,
                "network": network_io,
                "process": process_info
            }
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}
    
    async def analyze_database_performance(self, db: AsyncSession) -> Dict:
        """分析数据库性能"""
        try:
            metrics = {}
            
            # 查询统计信息
            query_stats = await self._get_query_statistics(db)
            metrics["query_stats"] = query_stats
            
            # 连接池状态
            pool_stats = await self._get_connection_pool_stats(db)
            metrics["pool_stats"] = pool_stats
            
            # 慢查询分析
            slow_queries = await self._analyze_slow_queries(db)
            metrics["slow_queries"] = slow_queries
            
            # 索引使用情况
            index_usage = await self._analyze_index_usage(db)
            metrics["index_usage"] = index_usage
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to analyze database performance: {e}")
            return {}
    
    async def _get_query_statistics(self, db: AsyncSession) -> Dict:
        """获取查询统计信息"""
        try:
            # 这里需要根据具体数据库类型实现
            # SQLite示例
            result = await db.execute(text("PRAGMA compile_options"))
            compile_options = [row[0] for row in result.fetchall()]
            
            return {
                "compile_options": compile_options,
                "total_queries": 0,  # 需要实际统计
                "avg_query_time": 0  # 需要实际计算
            }
        except Exception as e:
            logger.error(f"Failed to get query statistics: {e}")
            return {}
    
    async def _get_connection_pool_stats(self, db: AsyncSession) -> Dict:
        """获取连接池统计"""
        try:
            engine = db.get_bind()
            pool = engine.pool
            
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        except Exception as e:
            logger.error(f"Failed to get connection pool stats: {e}")
            return {}
    
    async def _analyze_slow_queries(self, db: AsyncSession) -> List[Dict]:
        """分析慢查询"""
        # 这里需要根据实际的慢查询日志实现
        # 目前返回模拟数据
        return []
    
    async def _analyze_index_usage(self, db: AsyncSession) -> Dict:
        """分析索引使用情况"""
        try:
            # SQLite示例
            result = await db.execute(text("""
                SELECT name, sql FROM sqlite_master 
                WHERE type = 'index' AND sql IS NOT NULL
            """))
            
            indexes = []
            for row in result.fetchall():
                indexes.append({
                    "name": row[0],
                    "sql": row[1]
                })
            
            return {
                "total_indexes": len(indexes),
                "indexes": indexes
            }
        except Exception as e:
            logger.error(f"Failed to analyze index usage: {e}")
            return {}
    
    async def generate_performance_report(self) -> Dict:
        """生成性能报告"""
        try:
            # 收集系统指标
            system_metrics = await self.collect_system_metrics()
            
            # 收集数据库指标
            async for db in get_db():
                db_metrics = await self.analyze_database_performance(db)
                break
            
            # 分析应用指标
            app_metrics = await self._analyze_application_metrics()
            
            # 生成建议
            recommendations = await self._generate_recommendations(
                system_metrics, db_metrics, app_metrics
            )
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": system_metrics,
                "database": db_metrics,
                "application": app_metrics,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {}
    
    async def _analyze_application_metrics(self) -> Dict:
        """分析应用性能指标"""
        try:
            # 从缓存或监控系统获取应用指标
            return {
                "avg_response_time": 0,
                "request_rate": 0,
                "error_rate": 0,
                "active_connections": 0
            }
        except Exception as e:
            logger.error(f"Failed to analyze application metrics: {e}")
            return {}
    
    async def _generate_recommendations(self, system_metrics: Dict, 
                                      db_metrics: Dict, app_metrics: Dict) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        try:
            # 系统资源建议
            if system_metrics.get("cpu", {}).get("percent", 0) > 80:
                recommendations.append("CPU使用率过高，建议优化计算密集型操作或增加CPU资源")
            
            if system_metrics.get("memory", {}).get("percent", 0) > 85:
                recommendations.append("内存使用率过高，建议检查内存泄漏或增加内存资源")
            
            if system_metrics.get("disk", {}).get("percent", 0) > 90:
                recommendations.append("磁盘空间不足，建议清理日志文件或扩展存储空间")
            
            # 数据库建议
            pool_stats = db_metrics.get("pool_stats", {})
            if pool_stats.get("checked_out", 0) > pool_stats.get("pool_size", 1) * 0.8:
                recommendations.append("数据库连接池使用率过高，建议增加连接池大小")
            
            # 应用建议
            if app_metrics.get("avg_response_time", 0) > 1000:
                recommendations.append("平均响应时间过长，建议优化API性能或添加缓存")
            
            if app_metrics.get("error_rate", 0) > 5:
                recommendations.append("错误率过高，建议检查应用日志并修复错误")
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
        
        return recommendations
    
    async def check_performance_alerts(self) -> List[Dict]:
        """检查性能告警"""
        alerts = []
        
        try:
            system_metrics = await self.collect_system_metrics()
            
            # 检查CPU告警
            cpu_percent = system_metrics.get("cpu", {}).get("percent", 0)
            if cpu_percent > self.alert_thresholds["cpu_usage"]:
                alerts.append({
                    "type": "cpu_high",
                    "severity": "warning",
                    "message": f"CPU使用率过高: {cpu_percent:.1f}%",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # 检查内存告警
            memory_percent = system_metrics.get("memory", {}).get("percent", 0)
            if memory_percent > 85:
                alerts.append({
                    "type": "memory_high",
                    "severity": "warning",
                    "message": f"内存使用率过高: {memory_percent:.1f}%",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # 检查磁盘告警
            disk_percent = system_metrics.get("disk", {}).get("percent", 0)
            if disk_percent > 90:
                alerts.append({
                    "type": "disk_full",
                    "severity": "critical",
                    "message": f"磁盘空间不足: {disk_percent:.1f}%",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Failed to check performance alerts: {e}")
        
        return alerts
    
    async def optimize_query(self, query: str) -> Dict:
        """查询优化建议"""
        try:
            suggestions = []
            
            # 基本查询优化建议
            if "SELECT *" in query.upper():
                suggestions.append("避免使用SELECT *，明确指定需要的列")
            
            if "ORDER BY" in query.upper() and "LIMIT" not in query.upper():
                suggestions.append("对大结果集排序时建议添加LIMIT限制")
            
            if query.upper().count("JOIN") > 3:
                suggestions.append("复杂的多表连接可能影响性能，考虑分解查询")
            
            if "WHERE" not in query.upper() and "SELECT" in query.upper():
                suggestions.append("考虑添加WHERE条件以减少查询数据量")
            
            return {
                "original_query": query,
                "suggestions": suggestions,
                "estimated_improvement": "10-30%"  # 估算值
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize query: {e}")
            return {"error": str(e)}
    
    async def benchmark_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """基准测试操作"""
        try:
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            # 执行操作
            if asyncio.iscoroutinefunction(operation_func):
                result = await operation_func(*args, **kwargs)
            else:
                result = operation_func(*args, **kwargs)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            benchmark_result = {
                "operation": operation_name,
                "execution_time": (end_time - start_time) * 1000,  # 毫秒
                "memory_usage": end_memory - start_memory,  # 字节
                "timestamp": datetime.utcnow().isoformat(),
                "success": True
            }
            
            logger.info(f"Benchmark {operation_name}: {benchmark_result['execution_time']:.2f}ms")
            
            return benchmark_result
            
        except Exception as e:
            logger.error(f"Benchmark failed for {operation_name}: {e}")
            return {
                "operation": operation_name,
                "error": str(e),
                "success": False,
                "timestamp": datetime.utcnow().isoformat()
            }
