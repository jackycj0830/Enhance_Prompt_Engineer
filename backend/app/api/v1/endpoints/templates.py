"""
模板管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from config.database import get_db
from app.models.user import User
from app.models.template import Template, TemplateRating, TemplateUsage
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/")
async def get_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_public: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取模板列表"""
    query = db.query(Template)
    
    if is_public:
        query = query.filter(Template.is_public == True)
    else:
        # 只显示用户自己的模板
        query = query.filter(Template.creator_id == current_user.id)
    
    if category:
        query = query.filter(Template.category == category)
    
    if is_featured is not None:
        query = query.filter(Template.is_featured == is_featured)
    
    templates = query.order_by(Template.rating.desc(), Template.usage_count.desc()).offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "items": [template.to_dict() for template in templates],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.post("/")
async def create_template(
    template_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新模板"""
    template = Template(
        creator_id=current_user.id,
        name=template_data["name"],
        description=template_data.get("description"),
        content=template_data["content"],
        category=template_data.get("category"),
        tags=template_data.get("tags", []),
        is_public=template_data.get("is_public", True),
        is_featured=False  # 只有管理员可以设置推荐
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template.to_dict()

@router.get("/{template_id}")
async def get_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定模板"""
    template = db.query(Template).filter(Template.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 检查访问权限
    if not template.is_public and template.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此模板"
        )
    
    return template.to_dict()

@router.put("/{template_id}")
async def update_template(
    template_id: UUID,
    template_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新模板"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.creator_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在或无权修改"
        )
    
    # 更新允许的字段
    allowed_fields = ["name", "description", "content", "category", "tags", "is_public"]
    for field, value in template_data.items():
        if field in allowed_fields:
            setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return template.to_dict()

@router.delete("/{template_id}")
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除模板"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.creator_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在或无权删除"
        )
    
    db.delete(template)
    db.commit()
    
    return {"message": "模板已删除"}

@router.post("/{template_id}/use")
async def use_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """使用模板"""
    template = db.query(Template).filter(Template.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 检查访问权限
    if not template.is_public and template.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权使用此模板"
        )
    
    # 记录使用
    usage = TemplateUsage(
        template_id=template_id,
        user_id=current_user.id
    )
    db.add(usage)
    
    # 增加使用计数
    template.usage_count += 1
    
    db.commit()
    
    return {
        "template": template.to_dict(),
        "message": "模板使用记录已保存"
    }

@router.post("/{template_id}/rate")
async def rate_template(
    template_id: UUID,
    rating_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """评价模板"""
    template = db.query(Template).filter(Template.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    rating_value = rating_data.get("rating")
    if not rating_value or rating_value < 1 or rating_value > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="评分必须在1-5之间"
        )
    
    # 检查是否已评价
    existing_rating = db.query(TemplateRating).filter(
        TemplateRating.template_id == template_id,
        TemplateRating.user_id == current_user.id
    ).first()
    
    if existing_rating:
        # 更新评价
        existing_rating.rating = rating_value
        existing_rating.comment = rating_data.get("comment")
        db.commit()
        db.refresh(existing_rating)
        rating_obj = existing_rating
    else:
        # 创建新评价
        rating_obj = TemplateRating(
            template_id=template_id,
            user_id=current_user.id,
            rating=rating_value,
            comment=rating_data.get("comment")
        )
        db.add(rating_obj)
        db.commit()
        db.refresh(rating_obj)
    
    # 重新计算平均评分
    avg_rating = db.query(TemplateRating).filter(
        TemplateRating.template_id == template_id
    ).with_entities(
        db.func.avg(TemplateRating.rating)
    ).scalar()
    
    template.rating = round(float(avg_rating), 2) if avg_rating else 0.0
    db.commit()
    
    return {
        "rating": rating_obj.to_dict(),
        "template_avg_rating": template.rating
    }

@router.get("/categories")
async def get_template_categories(db: Session = Depends(get_db)):
    """获取所有模板分类"""
    categories = db.query(Template.category).filter(
        Template.is_public == True,
        Template.category.isnot(None)
    ).distinct().all()
    
    return [cat[0] for cat in categories if cat[0]]
