"""
用户管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from config.database import get_db
from app.models.user import User, UserPreference
from app.schemas.auth import UserResponse
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """获取用户资料"""
    return UserResponse.from_orm(current_user)

@router.get("/preferences")
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户偏好设置"""
    preference = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()
    
    if not preference:
        # 如果没有偏好设置，创建默认设置
        preference = UserPreference(
            user_id=current_user.id,
            preferred_ai_model="gpt-3.5-turbo",
            analysis_depth="standard",
            notification_settings={"email": True, "push": False},
            ui_preferences={"theme": "light", "language": "zh-CN"}
        )
        db.add(preference)
        db.commit()
        db.refresh(preference)
    
    return preference.to_dict()

@router.put("/preferences")
async def update_user_preferences(
    preferences_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户偏好设置"""
    preference = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()
    
    if not preference:
        preference = UserPreference(user_id=current_user.id)
        db.add(preference)
    
    # 更新允许的字段
    allowed_fields = [
        'preferred_ai_model', 'analysis_depth', 
        'notification_settings', 'ui_preferences'
    ]
    
    for field, value in preferences_data.items():
        if field in allowed_fields:
            setattr(preference, field, value)
    
    db.commit()
    db.refresh(preference)
    
    return preference.to_dict()

@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户统计信息"""
    from app.models.prompt import Prompt, AnalysisResult
    from app.models.template import Template
    
    # 统计用户的提示词数量
    prompt_count = db.query(Prompt).filter(Prompt.user_id == current_user.id).count()
    
    # 统计分析次数
    analysis_count = db.query(AnalysisResult).join(Prompt).filter(
        Prompt.user_id == current_user.id
    ).count()
    
    # 统计创建的模板数量
    template_count = db.query(Template).filter(
        Template.creator_id == current_user.id
    ).count()
    
    return {
        "prompt_count": prompt_count,
        "analysis_count": analysis_count,
        "template_count": template_count,
        "user_since": current_user.created_at.isoformat() if current_user.created_at else None
    }
