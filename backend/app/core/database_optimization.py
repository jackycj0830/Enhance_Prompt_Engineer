"""
数据库性能优化工具
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from app.core.database import get_db
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseOptimizer:
    """数据库性能优化器"""
    
    def __init__(self):
        self.slow_queries: List[Dict] = []
        self.query_stats: Dict[str, Dict] = {}
    
    async def analyze_query_performance(self, db: AsyncSession) -> Dict:
        """分析查询性能"""
        try:
            analysis = {
                "slow_queries": await self._get_slow_queries(db),
                "index_usage": await self._analyze_index_usage(db),
                "table_stats": await self._get_table_statistics(db),
                "connection_stats": await self._get_connection_statistics(db),
                "recommendations": []
            }
            
            # 生成优化建议
            analysis["recommendations"] = await self._generate_optimization_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze query performance: {e}")
            return {}
    
    async def _get_slow_queries(self, db: AsyncSession) -> List[Dict]:
        """获取慢查询信息"""
        try:
            # 这里需要根据具体数据库类型实现
            # SQLite示例（实际生产环境建议使用PostgreSQL或MySQL）
            
            # 模拟慢查询数据
            slow_queries = []
            
            # 如果是PostgreSQL，可以查询pg_stat_statements
            # if settings.DATABASE_URL.startswith("postgresql"):
            #     result = await db.execute(text("""
            #         SELECT query, calls, total_time, mean_time, rows
            #         FROM pg_stat_statements
            #         WHERE mean_time > 100
            #         ORDER BY mean_time DESC
            #         LIMIT 10
            #     """))
            #     
            #     for row in result.fetchall():
            #         slow_queries.append({
            #             "query": row.query,
            #             "calls": row.calls,
            #             "total_time": row.total_time,
            #             "mean_time": row.mean_time,
            #             "rows": row.rows
            #         })
            
            return slow_queries
            
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []
    
    async def _analyze_index_usage(self, db: AsyncSession) -> Dict:
        """分析索引使用情况"""
        try:
            index_info = {
                "total_indexes": 0,
                "unused_indexes": [],
                "missing_indexes": [],
                "index_details": []
            }
            
            # SQLite索引信息
            result = await db.execute(text("""
                SELECT name, sql, tbl_name 
                FROM sqlite_master 
                WHERE type = 'index' AND sql IS NOT NULL
            """))
            
            indexes = result.fetchall()
            index_info["total_indexes"] = len(indexes)
            
            for index in indexes:
                index_info["index_details"].append({
                    "name": index.name,
                    "table": index.tbl_name,
                    "sql": index.sql
                })
            
            # 检查可能缺失的索引
            missing_indexes = await self._check_missing_indexes(db)
            index_info["missing_indexes"] = missing_indexes
            
            return index_info
            
        except Exception as e:
            logger.error(f"Failed to analyze index usage: {e}")
            return {}
    
    async def _check_missing_indexes(self, db: AsyncSession) -> List[Dict]:
        """检查可能缺失的索引"""
        missing_indexes = []
        
        try:
            # 检查常见的查询模式，建议添加索引
            common_patterns = [
                {
                    "table": "prompts",
                    "columns": ["user_id", "created_at"],
                    "reason": "用户提示词按时间排序查询"
                },
                {
                    "table": "templates",
                    "columns": ["category", "is_public"],
                    "reason": "按分类和公开状态筛选模板"
                },
                {
                    "table": "analyses",
                    "columns": ["user_id", "overall_score"],
                    "reason": "用户分析结果按评分排序"
                }
            ]
            
            for pattern in common_patterns:
                # 检查索引是否存在
                index_exists = await self._check_index_exists(
                    db, pattern["table"], pattern["columns"]
                )
                
                if not index_exists:
                    missing_indexes.append(pattern)
            
            return missing_indexes
            
        except Exception as e:
            logger.error(f"Failed to check missing indexes: {e}")
            return []
    
    async def _check_index_exists(self, db: AsyncSession, table: str, columns: List[str]) -> bool:
        """检查索引是否存在"""
        try:
            # 简化的索引检查逻辑
            index_name = f"idx_{table}_{'_'.join(columns)}"
            
            result = await db.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type = 'index' AND name = :index_name
            """), {"index_name": index_name})
            
            return result.fetchone() is not None
            
        except Exception as e:
            logger.error(f"Failed to check index existence: {e}")
            return False
    
    async def _get_table_statistics(self, db: AsyncSession) -> Dict:
        """获取表统计信息"""
        try:
            stats = {}
            
            tables = ["users", "prompts", "templates", "analyses"]
            
            for table in tables:
                try:
                    # 获取行数
                    result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    row_count = result.scalar()
                    
                    # 获取表大小（SQLite特定）
                    result = await db.execute(text(f"PRAGMA table_info({table})"))
                    columns = result.fetchall()
                    
                    stats[table] = {
                        "row_count": row_count,
                        "column_count": len(columns),
                        "columns": [col.name for col in columns]
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to get stats for table {table}: {e}")
                    stats[table] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return {}
    
    async def _get_connection_statistics(self, db: AsyncSession) -> Dict:
        """获取连接统计信息"""
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
            logger.error(f"Failed to get connection statistics: {e}")
            return {}
    
    async def _generate_optimization_recommendations(self, analysis: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        try:
            # 基于分析结果生成建议
            
            # 检查缺失的索引
            missing_indexes = analysis.get("index_usage", {}).get("missing_indexes", [])
            for index in missing_indexes:
                recommendations.append(
                    f"建议为表 {index['table']} 的列 {', '.join(index['columns'])} 添加索引: {index['reason']}"
                )
            
            # 检查表大小
            table_stats = analysis.get("table_stats", {})
            for table, stats in table_stats.items():
                if isinstance(stats, dict) and "row_count" in stats:
                    row_count = stats["row_count"]
                    if row_count > 100000:
                        recommendations.append(
                            f"表 {table} 数据量较大({row_count}行)，建议考虑分区或归档策略"
                        )
            
            # 检查连接池
            conn_stats = analysis.get("connection_stats", {})
            if conn_stats.get("checked_out", 0) > conn_stats.get("pool_size", 1) * 0.8:
                recommendations.append("数据库连接池使用率过高，建议增加连接池大小")
            
            # 检查慢查询
            slow_queries = analysis.get("slow_queries", [])
            if len(slow_queries) > 0:
                recommendations.append(f"发现 {len(slow_queries)} 个慢查询，建议优化查询语句或添加索引")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []
    
    async def optimize_query(self, query: str) -> Dict:
        """优化查询语句"""
        try:
            suggestions = []
            optimized_query = query
            
            # 基本查询优化规则
            query_upper = query.upper()
            
            # 检查SELECT *
            if "SELECT *" in query_upper:
                suggestions.append({
                    "type": "select_optimization",
                    "message": "避免使用 SELECT *，明确指定需要的列",
                    "impact": "medium"
                })
            
            # 检查WHERE子句
            if "SELECT" in query_upper and "WHERE" not in query_upper:
                suggestions.append({
                    "type": "where_clause",
                    "message": "考虑添加 WHERE 条件以减少查询数据量",
                    "impact": "high"
                })
            
            # 检查ORDER BY without LIMIT
            if "ORDER BY" in query_upper and "LIMIT" not in query_upper:
                suggestions.append({
                    "type": "limit_optimization",
                    "message": "对大结果集排序时建议添加 LIMIT 限制",
                    "impact": "medium"
                })
            
            # 检查复杂JOIN
            join_count = query_upper.count("JOIN")
            if join_count > 3:
                suggestions.append({
                    "type": "join_optimization",
                    "message": f"查询包含 {join_count} 个 JOIN，考虑分解为多个简单查询",
                    "impact": "high"
                })
            
            # 检查子查询
            if "(" in query and "SELECT" in query_upper:
                subquery_count = query_upper.count("(SELECT")
                if subquery_count > 0:
                    suggestions.append({
                        "type": "subquery_optimization",
                        "message": f"查询包含 {subquery_count} 个子查询，考虑使用 JOIN 替代",
                        "impact": "medium"
                    })
            
            return {
                "original_query": query,
                "optimized_query": optimized_query,
                "suggestions": suggestions,
                "estimated_improvement": self._estimate_improvement(suggestions)
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize query: {e}")
            return {"error": str(e)}
    
    def _estimate_improvement(self, suggestions: List[Dict]) -> str:
        """估算性能改进幅度"""
        if not suggestions:
            return "0%"
        
        high_impact = sum(1 for s in suggestions if s.get("impact") == "high")
        medium_impact = sum(1 for s in suggestions if s.get("impact") == "medium")
        
        if high_impact > 0:
            return "30-50%"
        elif medium_impact > 1:
            return "15-30%"
        elif medium_impact > 0:
            return "5-15%"
        else:
            return "1-5%"
    
    async def create_optimized_indexes(self, db: AsyncSession, recommendations: List[Dict]) -> Dict:
        """创建优化索引"""
        try:
            created_indexes = []
            failed_indexes = []
            
            for rec in recommendations:
                if rec.get("type") == "missing_index":
                    table = rec["table"]
                    columns = rec["columns"]
                    index_name = f"idx_{table}_{'_'.join(columns)}"
                    
                    try:
                        # 创建索引
                        create_sql = f"CREATE INDEX {index_name} ON {table} ({', '.join(columns)})"
                        await db.execute(text(create_sql))
                        await db.commit()
                        
                        created_indexes.append({
                            "name": index_name,
                            "table": table,
                            "columns": columns
                        })
                        
                    except Exception as e:
                        failed_indexes.append({
                            "name": index_name,
                            "error": str(e)
                        })
            
            return {
                "created_indexes": created_indexes,
                "failed_indexes": failed_indexes,
                "total_created": len(created_indexes)
            }
            
        except Exception as e:
            logger.error(f"Failed to create optimized indexes: {e}")
            return {"error": str(e)}


# 查询性能监控装饰器
def monitor_query_performance(query_name: str):
    """查询性能监控装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import time
            
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # 毫秒
                
                # 记录查询性能
                logger.info(f"Query {query_name} executed in {execution_time:.2f}ms")
                
                # 如果查询时间过长，记录警告
                if execution_time > 1000:  # 1秒
                    logger.warning(f"Slow query detected: {query_name} took {execution_time:.2f}ms")
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Query {query_name} failed after {execution_time:.2f}ms: {e}")
                raise
        
        return wrapper
    return decorator


# 全局数据库优化器实例
db_optimizer = DatabaseOptimizer()
