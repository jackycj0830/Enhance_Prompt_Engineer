"""
模板管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncio

from config.database import get_db
from app.models.user import User
from app.models.template import Template, TemplateRating, TemplateUsage, TemplateCategory, TemplateTag
from app.api.v1.endpoints.auth import get_current_user
from app.services.template_service import get_template_service

router = APIRouter()

@router.get("/", response_model=dict)
async def get_templates(
    query: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类"),
    tags: Optional[str] = Query(None, description="标签，逗号分隔"),
    industry: Optional[str] = Query(None, description="行业"),
    difficulty_level: Optional[str] = Query(None, description="难度级别"),
    language: Optional[str] = Query(None, description="语言"),
    is_featured: Optional[bool] = Query(None, description="是否推荐"),
    is_verified: Optional[bool] = Query(None, description="是否认证"),
    creator_id: Optional[str] = Query(None, description="创建者ID"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取模板列表"""
    template_service = get_template_service(db)

    # 处理标签参数
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    try:
        templates, total = await template_service.search_templates(
            query=query,
            category=category,
            tags=tag_list,
            industry=industry,
            difficulty_level=difficulty_level,
            language=language,
            is_featured=is_featured,
            is_verified=is_verified,
            creator_id=creator_id,
            user_id=str(current_user.id),
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )

        return {
            "templates": [template.to_dict(include_content=False) for template in templates],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板列表失败: {str(e)}"
        )

@router.post("/", response_model=dict)
async def create_template(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新模板"""
    template_service = get_template_service(db)

    try:
        template = await template_service.create_template(
            creator_id=str(current_user.id),
            name=request.get("name"),
            content=request.get("content"),
            description=request.get("description"),
            category=request.get("category"),
            tags=request.get("tags", []),
            industry=request.get("industry"),
            use_case=request.get("use_case"),
            difficulty_level=request.get("difficulty_level", "beginner"),
            is_public=request.get("is_public", True),
            metadata=request.get("metadata", {})
        )

        return {
            "template": template.to_dict(),
            "message": "模板创建成功"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

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

# 获取热门模板
@router.get("/popular/list", response_model=dict)
async def get_popular_templates(
    limit: int = Query(10, ge=1, le=50, description="数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取热门模板"""
    template_service = get_template_service(db)

    templates = await template_service.get_popular_templates(limit)

    return {
        "templates": [template.to_dict(include_content=False) for template in templates]
    }

# 获取推荐模板
@router.get("/featured/list", response_model=dict)
async def get_featured_templates(
    limit: int = Query(10, ge=1, le=50, description="数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取推荐模板"""
    template_service = get_template_service(db)

    templates = await template_service.get_featured_templates(limit)

    return {
        "templates": [template.to_dict(include_content=False) for template in templates]
    }

# 获取最新模板
@router.get("/recent/list", response_model=dict)
async def get_recent_templates(
    limit: int = Query(10, ge=1, le=50, description="数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取最新模板"""
    template_service = get_template_service(db)

    templates = await template_service.get_recent_templates(limit)

    return {
        "templates": [template.to_dict(include_content=False) for template in templates]
    }

# 获取分类列表
@router.get("/categories/list", response_model=dict)
async def get_categories(
    db: Session = Depends(get_db)
):
    """获取模板分类列表"""
    categories = db.query(TemplateCategory).filter(
        TemplateCategory.is_active == True
    ).order_by(TemplateCategory.sort_order, TemplateCategory.name).all()

    return {
        "categories": [category.to_dict() for category in categories]
    }

# 获取标签列表
@router.get("/tags/list", response_model=dict)
async def get_tags(
    featured_only: bool = Query(False, description="只获取推荐标签"),
    limit: int = Query(50, ge=1, le=200, description="数量限制"),
    db: Session = Depends(get_db)
):
    """获取模板标签列表"""
    query = db.query(TemplateTag)

    if featured_only:
        query = query.filter(TemplateTag.is_featured == True)

    tags = query.order_by(TemplateTag.usage_count.desc()).limit(limit).all()

    return {
        "tags": [tag.to_dict() for tag in tags]
    }
