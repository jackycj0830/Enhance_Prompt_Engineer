"""
提示词管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from config.database import get_db
from app.models.user import User
from app.models.prompt import Prompt, AnalysisResult
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/")
async def get_prompts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的提示词列表"""
    query = db.query(Prompt).filter(Prompt.user_id == current_user.id)
    
    if category:
        query = query.filter(Prompt.category == category)
    
    prompts = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "items": [prompt.to_dict() for prompt in prompts],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.post("/")
async def create_prompt(
    prompt_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新的提示词"""
    prompt = Prompt(
        user_id=current_user.id,
        title=prompt_data.get("title"),
        content=prompt_data["content"],
        category=prompt_data.get("category"),
        tags=prompt_data.get("tags", []),
        is_template=prompt_data.get("is_template", False),
        is_public=prompt_data.get("is_public", False)
    )
    
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    
    return prompt.to_dict()

@router.get("/{prompt_id}")
async def get_prompt(
    prompt_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定提示词"""
    prompt = db.query(Prompt).filter(
        Prompt.id == prompt_id,
        Prompt.user_id == current_user.id
    ).first()
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提示词不存在"
        )
    
    return prompt.to_dict()

@router.put("/{prompt_id}")
async def update_prompt(
    prompt_id: UUID,
    prompt_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新提示词"""
    prompt = db.query(Prompt).filter(
        Prompt.id == prompt_id,
        Prompt.user_id == current_user.id
    ).first()
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提示词不存在"
        )
    
    # 更新允许的字段
    allowed_fields = ["title", "content", "category", "tags", "is_template", "is_public"]
    for field, value in prompt_data.items():
        if field in allowed_fields:
            setattr(prompt, field, value)
    
    db.commit()
    db.refresh(prompt)
    
    return prompt.to_dict()

@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除提示词"""
    prompt = db.query(Prompt).filter(
        Prompt.id == prompt_id,
        Prompt.user_id == current_user.id
    ).first()
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提示词不存在"
        )
    
    db.delete(prompt)
    db.commit()
    
    return {"message": "提示词已删除"}

@router.get("/{prompt_id}/analysis")
async def get_prompt_analysis(
    prompt_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取提示词的分析结果"""
    prompt = db.query(Prompt).filter(
        Prompt.id == prompt_id,
        Prompt.user_id == current_user.id
    ).first()
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提示词不存在"
        )
    
    # 获取最新的分析结果
    analysis = db.query(AnalysisResult).filter(
        AnalysisResult.prompt_id == prompt_id
    ).order_by(AnalysisResult.created_at.desc()).first()
    
    if not analysis:
        return {"message": "暂无分析结果"}
    
    return analysis.to_dict()

@router.get("/categories")
async def get_prompt_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户提示词的所有分类"""
    categories = db.query(Prompt.category).filter(
        Prompt.user_id == current_user.id,
        Prompt.category.isnot(None)
    ).distinct().all()
    
    return [cat[0] for cat in categories if cat[0]]
