"""
监控服务层 - 处理性能监控相关的业务逻辑
"""

import asyncio
import psutil
import time
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta
import json

from app.models.monitoring import (
    SystemMetrics, APIMetrics, AIModelMetrics,
    UserActivityMetrics, AlertRule, Alert
)
from app.models.user import User


class MonitoringService:
    """监控服务类"""

    def __init__(self, db: Session):
        self.db = db

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            await self._record_metric("system.cpu.usage", cpu_percent, "percent", "gauge")

            # 内存使用情况
            memory = psutil.virtual_memory()
            await self._record_metric("system.memory.usage", memory.percent, "percent", "gauge")
            await self._record_metric("system.memory.available", memory.available / (1024**3), "GB", "gauge")
            await self._record_metric("system.memory.total", memory.total / (1024**3), "GB", "gauge")

            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            await self._record_metric("system.disk.usage", disk_percent, "percent", "gauge")
            await self._record_metric("system.disk.free", disk.free / (1024**3), "GB", "gauge")

            # 网络IO
            network = psutil.net_io_counters()
            await self._record_metric("system.network.bytes_sent", network.bytes_sent, "bytes", "counter")
            await self._record_metric("system.network.bytes_recv", network.bytes_recv, "bytes", "counter")

            # 进程数量
            process_count = len(psutil.pids())
            await self._record_metric("system.processes.count", process_count, "count", "gauge")

            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk_percent,
                "process_count": process_count,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"收集系统指标失败: {e}")
            return {}

    async def record_api_metrics(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        request_size: int = 0,
        response_size: int = 0,
        user_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        error_message: str = None
    ):
        """记录API调用指标"""
        try:
            metric = APIMetrics(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time=response_time,
                request_size=request_size,
                response_size=response_size,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=error_message
            )

            self.db.add(metric)
            self.db.commit()

            # 记录聚合指标
            await self._record_metric(f"api.{endpoint}.response_time", response_time, "seconds", "histogram")
            await self._record_metric(f"api.{endpoint}.requests", 1, "count", "counter")

            if status_code >= 400:
                await self._record_metric(f"api.{endpoint}.errors", 1, "count", "counter")

        except Exception as e:
            print(f"记录API指标失败: {e}")

    async def record_ai_model_metrics(
        self,
        model_name: str,
        provider: str,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        response_time: float,
        success: bool = True,
        error_type: str = None,
        error_message: str = None,
        user_id: str = None
    ):
        """记录AI模型调用指标"""
        try:
            total_tokens = input_tokens + output_tokens

            metric = AIModelMetrics(
                model_name=model_name,
                provider=provider,
                operation=operation,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost=cost,
                response_time=response_time,
                success=success,
                error_type=error_type,
                error_message=error_message,
                user_id=user_id
            )

            self.db.add(metric)
            self.db.commit()

            # 记录聚合指标
            await self._record_metric(f"ai.{provider}.{model_name}.tokens", total_tokens, "tokens", "counter")
            await self._record_metric(f"ai.{provider}.{model_name}.cost", cost, "USD", "counter")
            await self._record_metric(f"ai.{provider}.{model_name}.response_time", response_time, "seconds", "histogram")

            if not success:
                await self._record_metric(f"ai.{provider}.{model_name}.errors", 1, "count", "counter")

        except Exception as e:
            print(f"记录AI模型指标失败: {e}")

    async def record_user_activity(
        self,
        user_id: str,
        activity_type: str,
        activity_detail: str = None,
        resource_type: str = None,
        resource_id: str = None,
        metadata: Dict[str, Any] = None,
        session_id: str = None,
        ip_address: str = None
    ):
        """记录用户活动"""
        try:
            activity = UserActivityMetrics(
                user_id=user_id,
                activity_type=activity_type,
                activity_detail=activity_detail,
                resource_type=resource_type,
                resource_id=resource_id,
                metadata=metadata or {},
                session_id=session_id,
                ip_address=ip_address
            )

            self.db.add(activity)
            self.db.commit()

            # 记录聚合指标
            await self._record_metric(f"user.activity.{activity_type}", 1, "count", "counter")

        except Exception as e:
            print(f"记录用户活动失败: {e}")

    async def get_metrics_summary(
        self,
        time_range: str = "1h",
        metric_types: List[str] = None
    ) -> Dict[str, Any]:
        """获取指标摘要"""
        try:
            # 计算时间范围
            end_time = datetime.utcnow()
            if time_range == "1h":
                start_time = end_time - timedelta(hours=1)
            elif time_range == "24h":
                start_time = end_time - timedelta(hours=24)
            elif time_range == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_range == "30d":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=1)

            summary = {}

            # API指标摘要
            api_stats = self.db.query(
                func.count(APIMetrics.id).label('total_requests'),
                func.avg(APIMetrics.response_time).label('avg_response_time'),
                func.count(APIMetrics.id).filter(APIMetrics.status_code >= 400).label('error_count')
            ).filter(
                APIMetrics.timestamp >= start_time
            ).first()

            summary['api'] = {
                'total_requests': api_stats.total_requests or 0,
                'avg_response_time': float(api_stats.avg_response_time or 0),
                'error_count': api_stats.error_count or 0,
                'error_rate': (api_stats.error_count or 0) / max(api_stats.total_requests or 1, 1) * 100
            }

            # AI模型指标摘要
            ai_stats = self.db.query(
                func.count(AIModelMetrics.id).label('total_calls'),
                func.sum(AIModelMetrics.total_tokens).label('total_tokens'),
                func.sum(AIModelMetrics.cost).label('total_cost'),
                func.avg(AIModelMetrics.response_time).label('avg_response_time')
            ).filter(
                AIModelMetrics.timestamp >= start_time
            ).first()

            summary['ai'] = {
                'total_calls': ai_stats.total_calls or 0,
                'total_tokens': ai_stats.total_tokens or 0,
                'total_cost': float(ai_stats.total_cost or 0),
                'avg_response_time': float(ai_stats.avg_response_time or 0)
            }

            # 用户活动摘要
            user_stats = self.db.query(
                func.count(UserActivityMetrics.id).label('total_activities'),
                func.count(func.distinct(UserActivityMetrics.user_id)).label('active_users')
            ).filter(
                UserActivityMetrics.timestamp >= start_time
            ).first()

            summary['users'] = {
                'total_activities': user_stats.total_activities or 0,
                'active_users': user_stats.active_users or 0
            }

            # 系统指标摘要（最新值）
            latest_system_metrics = self.db.query(SystemMetrics).filter(
                SystemMetrics.metric_name.in_([
                    'system.cpu.usage',
                    'system.memory.usage',
                    'system.disk.usage'
                ])
            ).filter(
                SystemMetrics.timestamp >= start_time
            ).order_by(desc(SystemMetrics.timestamp)).limit(3).all()

            system_metrics = {}
            for metric in latest_system_metrics:
                system_metrics[metric.metric_name] = float(metric.metric_value)

            summary['system'] = system_metrics

            return summary

        except Exception as e:
            print(f"获取指标摘要失败: {e}")
            return {}

    async def get_time_series_data(
        self,
        metric_name: str,
        time_range: str = "1h",
        interval: str = "5m"
    ) -> List[Dict[str, Any]]:
        """获取时间序列数据"""
        try:
            # 计算时间范围
            end_time = datetime.utcnow()
            if time_range == "1h":
                start_time = end_time - timedelta(hours=1)
            elif time_range == "24h":
                start_time = end_time - timedelta(hours=24)
            elif time_range == "7d":
                start_time = end_time - timedelta(days=7)
            else:
                start_time = end_time - timedelta(hours=1)

            # 计算间隔
            if interval == "1m":
                interval_seconds = 60
            elif interval == "5m":
                interval_seconds = 300
            elif interval == "1h":
                interval_seconds = 3600
            else:
                interval_seconds = 300

            # 查询数据
            if metric_name.startswith('api.'):
                # API指标
                data = self.db.query(
                    func.date_trunc('minute', APIMetrics.timestamp).label('time_bucket'),
                    func.avg(APIMetrics.response_time).label('avg_value'),
                    func.count(APIMetrics.id).label('count')
                ).filter(
                    and_(
                        APIMetrics.timestamp >= start_time,
                        APIMetrics.endpoint == metric_name.replace('api.', '').split('.')[0]
                    )
                ).group_by('time_bucket').order_by('time_bucket').all()
            else:
                # 系统指标
                data = self.db.query(
                    func.date_trunc('minute', SystemMetrics.timestamp).label('time_bucket'),
                    func.avg(SystemMetrics.metric_value).label('avg_value'),
                    func.count(SystemMetrics.id).label('count')
                ).filter(
                    and_(
                        SystemMetrics.timestamp >= start_time,
                        SystemMetrics.metric_name == metric_name
                    )
                ).group_by('time_bucket').order_by('time_bucket').all()

            result = []
            for row in data:
                result.append({
                    'timestamp': row.time_bucket.isoformat(),
                    'value': float(row.avg_value or 0),
                    'count': row.count
                })

            return result

        except Exception as e:
            print(f"获取时间序列数据失败: {e}")
            return []

    async def _record_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: str,
        metric_type: str,
        tags: Dict[str, str] = None
    ):
        """记录指标"""
        try:
            metric = SystemMetrics(
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit,
                metric_type=metric_type,
                tags=tags or {}
            )

            self.db.add(metric)
            self.db.commit()

        except Exception as e:
            print(f"记录指标失败: {e}")

    async def check_alert_rules(self):
        """检查告警规则"""
        try:
            # 获取所有活跃的告警规则
            active_rules = self.db.query(AlertRule).filter(
                AlertRule.is_active == True
            ).all()

            for rule in active_rules:
                await self._evaluate_alert_rule(rule)

        except Exception as e:
            print(f"检查告警规则失败: {e}")

    async def _evaluate_alert_rule(self, rule: AlertRule):
        """评估单个告警规则"""
        try:
            # 获取最新的指标值
            latest_metric = self.db.query(SystemMetrics).filter(
                SystemMetrics.metric_name == rule.metric_name
            ).order_by(desc(SystemMetrics.timestamp)).first()

            if not latest_metric:
                return

            current_value = float(latest_metric.metric_value)
            threshold = float(rule.threshold)

            # 评估条件
            should_fire = False
            if rule.condition == ">":
                should_fire = current_value > threshold
            elif rule.condition == "<":
                should_fire = current_value < threshold
            elif rule.condition == ">=":
                should_fire = current_value >= threshold
            elif rule.condition == "<=":
                should_fire = current_value <= threshold
            elif rule.condition == "==":
                should_fire = current_value == threshold
            elif rule.condition == "!=":
                should_fire = current_value != threshold

            # 检查是否已有未解决的告警
            existing_alert = self.db.query(Alert).filter(
                and_(
                    Alert.rule_id == rule.id,
                    Alert.status == "firing"
                )
            ).first()

            if should_fire and not existing_alert:
                # 触发新告警
                alert = Alert(
                    rule_id=rule.id,
                    status="firing",
                    message=f"{rule.name}: {rule.metric_name} {rule.condition} {threshold} (当前值: {current_value})",
                    current_value=current_value,
                    threshold_value=threshold,
                    severity=rule.severity
                )
                self.db.add(alert)
                self.db.commit()

            elif not should_fire and existing_alert:
                # 解决告警
                existing_alert.status = "resolved"
                existing_alert.resolved_at = datetime.utcnow()
                self.db.commit()

        except Exception as e:
            print(f"评估告警规则失败: {e}")


def get_monitoring_service(db: Session) -> MonitoringService:
    """获取监控服务实例"""
    return MonitoringService(db)


class MonitoringService:
    """监控服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            await self._record_metric("system.cpu.usage", cpu_percent, "percent", "gauge")
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            await self._record_metric("system.memory.usage", memory.percent, "percent", "gauge")
            await self._record_metric("system.memory.available", memory.available / (1024**3), "GB", "gauge")
            await self._record_metric("system.memory.total", memory.total / (1024**3), "GB", "gauge")
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            await self._record_metric("system.disk.usage", disk_percent, "percent", "gauge")
            await self._record_metric("system.disk.free", disk.free / (1024**3), "GB", "gauge")
            
            # 网络IO
            network = psutil.net_io_counters()
            await self._record_metric("system.network.bytes_sent", network.bytes_sent, "bytes", "counter")
            await self._record_metric("system.network.bytes_recv", network.bytes_recv, "bytes", "counter")
            
            # 进程数量
            process_count = len(psutil.pids())
            await self._record_metric("system.processes.count", process_count, "count", "gauge")
            
            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk_percent,
                "process_count": process_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"收集系统指标失败: {e}")
            return {}
    
    async def record_api_metrics(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        request_size: int = 0,
        response_size: int = 0,
        user_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        error_message: str = None
    ):
        """记录API调用指标"""
        try:
            metric = APIMetrics(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time=response_time,
                request_size=request_size,
                response_size=response_size,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=error_message
            )
            
            self.db.add(metric)
            self.db.commit()
            
            # 记录聚合指标
            await self._record_metric(f"api.{endpoint}.response_time", response_time, "seconds", "histogram")
            await self._record_metric(f"api.{endpoint}.requests", 1, "count", "counter")
            
            if status_code >= 400:
                await self._record_metric(f"api.{endpoint}.errors", 1, "count", "counter")
            
        except Exception as e:
            print(f"记录API指标失败: {e}")
    
    async def record_ai_model_metrics(
        self,
        model_name: str,
        provider: str,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        response_time: float,
        success: bool = True,
        error_type: str = None,
        error_message: str = None,
        user_id: str = None
    ):
        """记录AI模型调用指标"""
        try:
            total_tokens = input_tokens + output_tokens
            
            metric = AIModelMetrics(
                model_name=model_name,
                provider=provider,
                operation=operation,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost=cost,
                response_time=response_time,
                success=success,
                error_type=error_type,
                error_message=error_message,
                user_id=user_id
            )
            
            self.db.add(metric)
            self.db.commit()
            
            # 记录聚合指标
            await self._record_metric(f"ai.{provider}.{model_name}.tokens", total_tokens, "tokens", "counter")
            await self._record_metric(f"ai.{provider}.{model_name}.cost", cost, "USD", "counter")
            await self._record_metric(f"ai.{provider}.{model_name}.response_time", response_time, "seconds", "histogram")
            
            if not success:
                await self._record_metric(f"ai.{provider}.{model_name}.errors", 1, "count", "counter")
            
        except Exception as e:
            print(f"记录AI模型指标失败: {e}")
    
    async def record_user_activity(
        self,
        user_id: str,
        activity_type: str,
        activity_detail: str = None,
        resource_type: str = None,
        resource_id: str = None,
        metadata: Dict[str, Any] = None,
        session_id: str = None,
        ip_address: str = None
    ):
        """记录用户活动"""
        try:
            activity = UserActivityMetrics(
                user_id=user_id,
                activity_type=activity_type,
                activity_detail=activity_detail,
                resource_type=resource_type,
                resource_id=resource_id,
                metadata=metadata or {},
                session_id=session_id,
                ip_address=ip_address
            )
            
            self.db.add(activity)
            self.db.commit()
            
            # 记录聚合指标
            await self._record_metric(f"user.activity.{activity_type}", 1, "count", "counter")
            
        except Exception as e:
            print(f"记录用户活动失败: {e}")
    
    async def get_metrics_summary(
        self,
        time_range: str = "1h",
        metric_types: List[str] = None
    ) -> Dict[str, Any]:
        """获取指标摘要"""
        try:
            # 计算时间范围
            end_time = datetime.utcnow()
            if time_range == "1h":
                start_time = end_time - timedelta(hours=1)
            elif time_range == "24h":
                start_time = end_time - timedelta(hours=24)
            elif time_range == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_range == "30d":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=1)
            
            summary = {}
            
            # API指标摘要
            api_stats = self.db.query(
                func.count(APIMetrics.id).label('total_requests'),
                func.avg(APIMetrics.response_time).label('avg_response_time'),
                func.count(APIMetrics.id).filter(APIMetrics.status_code >= 400).label('error_count')
            ).filter(
                APIMetrics.timestamp >= start_time
            ).first()
            
            summary['api'] = {
                'total_requests': api_stats.total_requests or 0,
                'avg_response_time': float(api_stats.avg_response_time or 0),
                'error_count': api_stats.error_count or 0,
                'error_rate': (api_stats.error_count or 0) / max(api_stats.total_requests or 1, 1) * 100
            }
            
            # AI模型指标摘要
            ai_stats = self.db.query(
                func.count(AIModelMetrics.id).label('total_calls'),
                func.sum(AIModelMetrics.total_tokens).label('total_tokens'),
                func.sum(AIModelMetrics.cost).label('total_cost'),
                func.avg(AIModelMetrics.response_time).label('avg_response_time')
            ).filter(
                AIModelMetrics.timestamp >= start_time
            ).first()
            
            summary['ai'] = {
                'total_calls': ai_stats.total_calls or 0,
                'total_tokens': ai_stats.total_tokens or 0,
                'total_cost': float(ai_stats.total_cost or 0),
                'avg_response_time': float(ai_stats.avg_response_time or 0)
            }
            
            # 用户活动摘要
            user_stats = self.db.query(
                func.count(UserActivityMetrics.id).label('total_activities'),
                func.count(func.distinct(UserActivityMetrics.user_id)).label('active_users')
            ).filter(
                UserActivityMetrics.timestamp >= start_time
            ).first()
            
            summary['users'] = {
                'total_activities': user_stats.total_activities or 0,
                'active_users': user_stats.active_users or 0
            }
            
            # 系统指标摘要（最新值）
            latest_system_metrics = self.db.query(SystemMetrics).filter(
                SystemMetrics.metric_name.in_([
                    'system.cpu.usage',
                    'system.memory.usage',
                    'system.disk.usage'
                ])
            ).filter(
                SystemMetrics.timestamp >= start_time
            ).order_by(desc(SystemMetrics.timestamp)).limit(3).all()
            
            system_metrics = {}
            for metric in latest_system_metrics:
                system_metrics[metric.metric_name] = float(metric.metric_value)
            
            summary['system'] = system_metrics
            
            return summary
            
        except Exception as e:
            print(f"获取指标摘要失败: {e}")
            return {}
    
    async def get_time_series_data(
        self,
        metric_name: str,
        time_range: str = "1h",
        interval: str = "5m"
    ) -> List[Dict[str, Any]]:
        """获取时间序列数据"""
        try:
            # 计算时间范围
            end_time = datetime.utcnow()
            if time_range == "1h":
                start_time = end_time - timedelta(hours=1)
            elif time_range == "24h":
                start_time = end_time - timedelta(hours=24)
            elif time_range == "7d":
                start_time = end_time - timedelta(days=7)
            else:
                start_time = end_time - timedelta(hours=1)
            
            # 计算间隔
            if interval == "1m":
                interval_seconds = 60
            elif interval == "5m":
                interval_seconds = 300
            elif interval == "1h":
                interval_seconds = 3600
            else:
                interval_seconds = 300
            
            # 查询数据
            if metric_name.startswith('api.'):
                # API指标
                data = self.db.query(
                    func.date_trunc('minute', APIMetrics.timestamp).label('time_bucket'),
                    func.avg(APIMetrics.response_time).label('avg_value'),
                    func.count(APIMetrics.id).label('count')
                ).filter(
                    and_(
                        APIMetrics.timestamp >= start_time,
                        APIMetrics.endpoint == metric_name.replace('api.', '').split('.')[0]
                    )
                ).group_by('time_bucket').order_by('time_bucket').all()
            else:
                # 系统指标
                data = self.db.query(
                    func.date_trunc('minute', SystemMetrics.timestamp).label('time_bucket'),
                    func.avg(SystemMetrics.metric_value).label('avg_value'),
                    func.count(SystemMetrics.id).label('count')
                ).filter(
                    and_(
                        SystemMetrics.timestamp >= start_time,
                        SystemMetrics.metric_name == metric_name
                    )
                ).group_by('time_bucket').order_by('time_bucket').all()
            
            result = []
            for row in data:
                result.append({
                    'timestamp': row.time_bucket.isoformat(),
                    'value': float(row.avg_value or 0),
                    'count': row.count
                })
            
            return result
            
        except Exception as e:
            print(f"获取时间序列数据失败: {e}")
            return []
    
    async def _record_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: str,
        metric_type: str,
        tags: Dict[str, str] = None
    ):
        """记录指标"""
        try:
            metric = SystemMetrics(
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit,
                metric_type=metric_type,
                tags=tags or {}
            )
            
            self.db.add(metric)
            self.db.commit()
            
        except Exception as e:
            print(f"记录指标失败: {e}")
    
    async def check_alert_rules(self):
        """检查告警规则"""
        try:
            # 获取所有活跃的告警规则
            active_rules = self.db.query(AlertRule).filter(
                AlertRule.is_active == True
            ).all()
            
            for rule in active_rules:
                await self._evaluate_alert_rule(rule)
                
        except Exception as e:
            print(f"检查告警规则失败: {e}")
    
    async def _evaluate_alert_rule(self, rule: AlertRule):
        """评估单个告警规则"""
        try:
            # 获取最新的指标值
            latest_metric = self.db.query(SystemMetrics).filter(
                SystemMetrics.metric_name == rule.metric_name
            ).order_by(desc(SystemMetrics.timestamp)).first()
            
            if not latest_metric:
                return
            
            current_value = float(latest_metric.metric_value)
            threshold = float(rule.threshold)
            
            # 评估条件
            should_fire = False
            if rule.condition == ">":
                should_fire = current_value > threshold
            elif rule.condition == "<":
                should_fire = current_value < threshold
            elif rule.condition == ">=":
                should_fire = current_value >= threshold
            elif rule.condition == "<=":
                should_fire = current_value <= threshold
            elif rule.condition == "==":
                should_fire = current_value == threshold
            elif rule.condition == "!=":
                should_fire = current_value != threshold
            
            # 检查是否已有未解决的告警
            existing_alert = self.db.query(Alert).filter(
                and_(
                    Alert.rule_id == rule.id,
                    Alert.status == "firing"
                )
            ).first()
            
            if should_fire and not existing_alert:
                # 触发新告警
                alert = Alert(
                    rule_id=rule.id,
                    status="firing",
                    message=f"{rule.name}: {rule.metric_name} {rule.condition} {threshold} (当前值: {current_value})",
                    current_value=current_value,
                    threshold_value=threshold,
                    severity=rule.severity
                )
                self.db.add(alert)
                self.db.commit()
                
            elif not should_fire and existing_alert:
                # 解决告警
                existing_alert.status = "resolved"
                existing_alert.resolved_at = datetime.utcnow()
                self.db.commit()
                
        except Exception as e:
            print(f"评估告警规则失败: {e}")


def get_monitoring_service(db: Session) -> MonitoringService:
    """获取监控服务实例"""
    return MonitoringService(db)
