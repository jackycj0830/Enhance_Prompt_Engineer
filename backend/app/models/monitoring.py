"""
性能监控相关数据模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from config.database import Base

class SystemMetrics(Base):
    """系统指标表"""
    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False)  # 指标名称
    metric_value = Column(Numeric(15, 4), nullable=False)  # 指标值
    metric_unit = Column(String(20), nullable=True)  # 单位
    metric_type = Column(String(50), nullable=False)  # 指标类型: counter, gauge, histogram
    tags = Column(JSONB, default={})  # 标签信息
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # 索引
    __table_args__ = (
        Index('idx_system_metrics_name', 'metric_name'),
        Index('idx_system_metrics_type', 'metric_type'),
        Index('idx_system_metrics_timestamp', 'timestamp'),
        Index('idx_system_metrics_name_timestamp', 'metric_name', 'timestamp'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "metric_name": self.metric_name,
            "metric_value": float(self.metric_value),
            "metric_unit": self.metric_unit,
            "metric_type": self.metric_type,
            "tags": self.tags or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class APIMetrics(Base):
    """API调用指标表"""
    __tablename__ = "api_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint = Column(String(200), nullable=False)  # API端点
    method = Column(String(10), nullable=False)  # HTTP方法
    status_code = Column(Integer, nullable=False)  # 响应状态码
    response_time = Column(Numeric(10, 4), nullable=False)  # 响应时间(秒)
    request_size = Column(Integer, default=0)  # 请求大小(字节)
    response_size = Column(Integer, default=0)  # 响应大小(字节)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IP地址
    user_agent = Column(Text, nullable=True)  # 用户代理
    error_message = Column(Text, nullable=True)  # 错误信息
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        Index('idx_api_metrics_endpoint', 'endpoint'),
        Index('idx_api_metrics_status', 'status_code'),
        Index('idx_api_metrics_timestamp', 'timestamp'),
        Index('idx_api_metrics_user', 'user_id'),
        Index('idx_api_metrics_endpoint_timestamp', 'endpoint', 'timestamp'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "response_time": float(self.response_time),
            "request_size": self.request_size,
            "response_size": self.response_size,
            "user_id": str(self.user_id) if self.user_id else None,
            "ip_address": self.ip_address,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class AIModelMetrics(Base):
    """AI模型调用指标表"""
    __tablename__ = "ai_model_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)  # 模型名称
    provider = Column(String(50), nullable=False)  # 提供商: openai, anthropic
    operation = Column(String(50), nullable=False)  # 操作类型: completion, analysis
    input_tokens = Column(Integer, default=0)  # 输入token数
    output_tokens = Column(Integer, default=0)  # 输出token数
    total_tokens = Column(Integer, default=0)  # 总token数
    cost = Column(Numeric(10, 6), default=0.0)  # 成本(美元)
    response_time = Column(Numeric(10, 4), nullable=False)  # 响应时间(秒)
    success = Column(Boolean, default=True)  # 是否成功
    error_type = Column(String(100), nullable=True)  # 错误类型
    error_message = Column(Text, nullable=True)  # 错误信息
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        Index('idx_ai_metrics_model', 'model_name'),
        Index('idx_ai_metrics_provider', 'provider'),
        Index('idx_ai_metrics_operation', 'operation'),
        Index('idx_ai_metrics_timestamp', 'timestamp'),
        Index('idx_ai_metrics_user', 'user_id'),
        Index('idx_ai_metrics_success', 'success'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "model_name": self.model_name,
            "provider": self.provider,
            "operation": self.operation,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost": float(self.cost),
            "response_time": float(self.response_time),
            "success": self.success,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "user_id": str(self.user_id) if self.user_id else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class UserActivityMetrics(Base):
    """用户活动指标表"""
    __tablename__ = "user_activity_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # 活动类型
    activity_detail = Column(String(200), nullable=True)  # 活动详情
    resource_type = Column(String(50), nullable=True)  # 资源类型: prompt, template, analysis
    resource_id = Column(UUID(as_uuid=True), nullable=True)  # 资源ID
    metadata = Column(JSONB, default={})  # 额外元数据
    session_id = Column(String(100), nullable=True)  # 会话ID
    ip_address = Column(String(45), nullable=True)  # IP地址
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        Index('idx_user_activity_user', 'user_id'),
        Index('idx_user_activity_type', 'activity_type'),
        Index('idx_user_activity_timestamp', 'timestamp'),
        Index('idx_user_activity_resource', 'resource_type', 'resource_id'),
        Index('idx_user_activity_session', 'session_id'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "activity_type": self.activity_type,
            "activity_detail": self.activity_detail,
            "resource_type": self.resource_type,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "metadata": self.metadata or {},
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class AlertRule(Base):
    """告警规则表"""
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)  # 规则名称
    description = Column(Text, nullable=True)  # 规则描述
    metric_name = Column(String(100), nullable=False)  # 监控指标
    condition = Column(String(20), nullable=False)  # 条件: >, <, >=, <=, ==, !=
    threshold = Column(Numeric(15, 4), nullable=False)  # 阈值
    duration = Column(Integer, default=300)  # 持续时间(秒)
    severity = Column(String(20), default="warning")  # 严重程度: info, warning, error, critical
    is_active = Column(Boolean, default=True)  # 是否启用
    notification_channels = Column(JSONB, default=[])  # 通知渠道
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    creator = relationship("User")
    alerts = relationship("Alert", back_populates="rule", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_alert_rules_metric', 'metric_name'),
        Index('idx_alert_rules_active', 'is_active'),
        Index('idx_alert_rules_severity', 'severity'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "metric_name": self.metric_name,
            "condition": self.condition,
            "threshold": float(self.threshold),
            "duration": self.duration,
            "severity": self.severity,
            "is_active": self.is_active,
            "notification_channels": self.notification_channels or [],
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Alert(Base):
    """告警记录表"""
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="firing")  # 状态: firing, resolved
    message = Column(Text, nullable=False)  # 告警消息
    current_value = Column(Numeric(15, 4), nullable=False)  # 当前值
    threshold_value = Column(Numeric(15, 4), nullable=False)  # 阈值
    severity = Column(String(20), nullable=False)  # 严重程度
    fired_at = Column(DateTime(timezone=True), server_default=func.now())  # 触发时间
    resolved_at = Column(DateTime(timezone=True), nullable=True)  # 解决时间
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)  # 确认时间
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # 关系
    rule = relationship("AlertRule", back_populates="alerts")
    acknowledger = relationship("User")
    
    # 索引
    __table_args__ = (
        Index('idx_alerts_rule', 'rule_id'),
        Index('idx_alerts_status', 'status'),
        Index('idx_alerts_severity', 'severity'),
        Index('idx_alerts_fired_at', 'fired_at'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "rule_id": str(self.rule_id),
            "status": self.status,
            "message": self.message,
            "current_value": float(self.current_value),
            "threshold_value": float(self.threshold_value),
            "severity": self.severity,
            "fired_at": self.fired_at.isoformat() if self.fired_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": str(self.acknowledged_by) if self.acknowledged_by else None
        }
