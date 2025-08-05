"""
监控API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncio

from config.database import get_db
from app.models.user import User
from app.models.monitoring import SystemMetrics, APIMetrics, AIModelMetrics, AlertRule, Alert
from app.api.v1.endpoints.auth import get_current_user
from app.services.monitoring_service import get_monitoring_service

router = APIRouter()

# 获取监控概览
@router.get("/overview", response_model=dict)
async def get_monitoring_overview(
    time_range: str = Query("1h", description="时间范围: 1h, 24h, 7d, 30d"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取监控概览数据"""
    monitoring_service = get_monitoring_service(db)
    
    try:
        summary = await monitoring_service.get_metrics_summary(time_range)
        return {
            "summary": summary,
            "time_range": time_range,
            "timestamp": "2024-01-01T00:00:00Z"  # 当前时间
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取监控概览失败: {str(e)}"
        )

# 获取系统指标
@router.get("/system/metrics", response_model=dict)
async def get_system_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实时系统指标"""
    monitoring_service = get_monitoring_service(db)
    
    try:
        metrics = await monitoring_service.collect_system_metrics()
        return {
            "metrics": metrics,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统指标失败: {str(e)}"
        )

# 获取时间序列数据
@router.get("/metrics/timeseries", response_model=dict)
async def get_metrics_timeseries(
    metric_name: str = Query(..., description="指标名称"),
    time_range: str = Query("1h", description="时间范围"),
    interval: str = Query("5m", description="时间间隔"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指标时间序列数据"""
    monitoring_service = get_monitoring_service(db)
    
    try:
        data = await monitoring_service.get_time_series_data(
            metric_name=metric_name,
            time_range=time_range,
            interval=interval
        )
        
        return {
            "metric_name": metric_name,
            "time_range": time_range,
            "interval": interval,
            "data": data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取时间序列数据失败: {str(e)}"
        )

# 获取API指标
@router.get("/api/metrics", response_model=dict)
async def get_api_metrics(
    endpoint: Optional[str] = Query(None, description="API端点"),
    time_range: str = Query("1h", description="时间范围"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取API调用指标"""
    try:
        query = db.query(APIMetrics)
        
        if endpoint:
            query = query.filter(APIMetrics.endpoint.ilike(f"%{endpoint}%"))
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        metrics = query.order_by(APIMetrics.timestamp.desc()).offset(offset).limit(page_size).all()
        
        return {
            "metrics": [metric.to_dict() for metric in metrics],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取API指标失败: {str(e)}"
        )

# 获取AI模型指标
@router.get("/ai/metrics", response_model=dict)
async def get_ai_metrics(
    provider: Optional[str] = Query(None, description="AI提供商"),
    model_name: Optional[str] = Query(None, description="模型名称"),
    time_range: str = Query("1h", description="时间范围"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取AI模型调用指标"""
    try:
        query = db.query(AIModelMetrics)
        
        if provider:
            query = query.filter(AIModelMetrics.provider == provider)
        
        if model_name:
            query = query.filter(AIModelMetrics.model_name.ilike(f"%{model_name}%"))
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        metrics = query.order_by(AIModelMetrics.timestamp.desc()).offset(offset).limit(page_size).all()
        
        return {
            "metrics": [metric.to_dict() for metric in metrics],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取AI指标失败: {str(e)}"
        )

# 记录API指标（内部使用）
@router.post("/api/metrics", response_model=dict)
async def record_api_metric(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """记录API调用指标（内部使用）"""
    monitoring_service = get_monitoring_service(db)
    
    try:
        background_tasks.add_task(
            monitoring_service.record_api_metrics,
            endpoint=request.get("endpoint"),
            method=request.get("method"),
            status_code=request.get("status_code"),
            response_time=request.get("response_time"),
            request_size=request.get("request_size", 0),
            response_size=request.get("response_size", 0),
            user_id=request.get("user_id"),
            ip_address=request.get("ip_address"),
            user_agent=request.get("user_agent"),
            error_message=request.get("error_message")
        )
        
        return {"message": "API指标记录任务已提交"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"记录API指标失败: {str(e)}"
        )

# 获取告警规则
@router.get("/alerts/rules", response_model=dict)
async def get_alert_rules(
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取告警规则列表"""
    try:
        query = db.query(AlertRule)
        
        if is_active is not None:
            query = query.filter(AlertRule.is_active == is_active)
        
        rules = query.order_by(AlertRule.created_at.desc()).all()
        
        return {
            "rules": [rule.to_dict() for rule in rules]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取告警规则失败: {str(e)}"
        )

# 创建告警规则
@router.post("/alerts/rules", response_model=dict)
async def create_alert_rule(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建告警规则"""
    try:
        rule = AlertRule(
            name=request.get("name"),
            description=request.get("description"),
            metric_name=request.get("metric_name"),
            condition=request.get("condition"),
            threshold=request.get("threshold"),
            duration=request.get("duration", 300),
            severity=request.get("severity", "warning"),
            notification_channels=request.get("notification_channels", []),
            created_by=current_user.id
        )
        
        db.add(rule)
        db.commit()
        db.refresh(rule)
        
        return {
            "rule": rule.to_dict(),
            "message": "告警规则创建成功"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建告警规则失败: {str(e)}"
        )

# 获取告警列表
@router.get("/alerts", response_model=dict)
async def get_alerts(
    status_filter: Optional[str] = Query(None, description="状态筛选: firing, resolved"),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取告警列表"""
    try:
        query = db.query(Alert)
        
        if status_filter:
            query = query.filter(Alert.status == status_filter)
        
        if severity:
            query = query.filter(Alert.severity == severity)
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        alerts = query.order_by(Alert.fired_at.desc()).offset(offset).limit(page_size).all()
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取告警列表失败: {str(e)}"
        )

# 确认告警
@router.post("/alerts/{alert_id}/acknowledge", response_model=dict)
async def acknowledge_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """确认告警"""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="告警不存在"
            )
        
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = current_user.id
        
        db.commit()
        
        return {
            "message": "告警已确认",
            "alert": alert.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认告警失败: {str(e)}"
        )

# 获取监控统计
@router.get("/stats", response_model=dict)
async def get_monitoring_stats(
    time_range: str = Query("24h", description="时间范围"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取监控统计数据"""
    try:
        from datetime import datetime, timedelta
        
        # 计算时间范围
        end_time = datetime.utcnow()
        if time_range == "1h":
            start_time = end_time - timedelta(hours=1)
        elif time_range == "24h":
            start_time = end_time - timedelta(hours=24)
        elif time_range == "7d":
            start_time = end_time - timedelta(days=7)
        else:
            start_time = end_time - timedelta(hours=24)
        
        # 统计数据
        stats = {
            "api_calls": db.query(APIMetrics).filter(
                APIMetrics.timestamp >= start_time
            ).count(),
            "ai_calls": db.query(AIModelMetrics).filter(
                AIModelMetrics.timestamp >= start_time
            ).count(),
            "active_alerts": db.query(Alert).filter(
                Alert.status == "firing"
            ).count(),
            "total_alerts": db.query(Alert).filter(
                Alert.fired_at >= start_time
            ).count()
        }
        
        return {
            "stats": stats,
            "time_range": time_range
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取监控统计失败: {str(e)}"
        )
