"""
模板服务层 - 处理模板相关的业务逻辑
"""

import asyncio
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import re

from app.models.template import Template, TemplateRating, TemplateUsage, TemplateCollection, TemplateCategory, TemplateTag
from app.models.user import User


class TemplateService:
    """模板服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_template(
        self, 
        creator_id: str, 
        name: str, 
        content: str,
        description: str = None,
        category: str = None,
        tags: List[str] = None,
        industry: str = None,
        use_case: str = None,
        difficulty_level: str = "beginner",
        is_public: bool = True,
        metadata: Dict[str, Any] = None
    ) -> Template:
        """创建新模板"""
        try:
            template = Template(
                creator_id=creator_id,
                name=name,
                content=content,
                description=description,
                category=category,
                tags=tags or [],
                industry=industry,
                use_case=use_case,
                difficulty_level=difficulty_level,
                is_public=is_public,
                metadata=metadata or {}
            )
            
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            
            # 更新标签使用统计
            if tags:
                await self._update_tag_usage(tags)
            
            return template
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"创建模板失败: {str(e)}")
    
    async def get_template(self, template_id: str, user_id: str = None) -> Optional[Template]:
        """获取单个模板"""
        query = self.db.query(Template).filter(Template.id == template_id)
        
        # 如果不是创建者，只能查看公开模板
        if user_id:
            query = query.filter(
                or_(
                    Template.creator_id == user_id,
                    Template.is_public == True
                )
            )
        else:
            query = query.filter(Template.is_public == True)
        
        return query.first()
    
    async def update_template(
        self,
        template_id: str,
        user_id: str,
        **updates
    ) -> Optional[Template]:
        """更新模板"""
        template = self.db.query(Template).filter(
            and_(
                Template.id == template_id,
                Template.creator_id == user_id
            )
        ).first()
        
        if not template:
            return None
        
        # 更新字段
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            self.db.refresh(template)
            
            # 如果更新了标签，更新标签统计
            if 'tags' in updates:
                await self._update_tag_usage(updates['tags'])
            
            return template
            
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"更新模板失败: {str(e)}")
    
    async def delete_template(self, template_id: str, user_id: str) -> bool:
        """删除模板"""
        template = self.db.query(Template).filter(
            and_(
                Template.id == template_id,
                Template.creator_id == user_id
            )
        ).first()
        
        if not template:
            return False
        
        try:
            self.db.delete(template)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"删除模板失败: {str(e)}")
    
    async def search_templates(
        self,
        query: str = None,
        category: str = None,
        tags: List[str] = None,
        industry: str = None,
        difficulty_level: str = None,
        language: str = None,
        is_featured: bool = None,
        is_verified: bool = None,
        creator_id: str = None,
        user_id: str = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Template], int]:
        """搜索模板"""
        
        # 基础查询
        base_query = self.db.query(Template)
        
        # 权限过滤
        if user_id:
            base_query = base_query.filter(
                or_(
                    Template.creator_id == user_id,
                    Template.is_public == True
                )
            )
        else:
            base_query = base_query.filter(Template.is_public == True)
        
        # 文本搜索
        if query:
            search_filter = or_(
                Template.name.ilike(f"%{query}%"),
                Template.description.ilike(f"%{query}%"),
                Template.content.ilike(f"%{query}%")
            )
            base_query = base_query.filter(search_filter)
        
        # 分类过滤
        if category:
            base_query = base_query.filter(Template.category == category)
        
        # 标签过滤
        if tags:
            for tag in tags:
                base_query = base_query.filter(Template.tags.contains([tag]))
        
        # 行业过滤
        if industry:
            base_query = base_query.filter(Template.industry == industry)
        
        # 难度过滤
        if difficulty_level:
            base_query = base_query.filter(Template.difficulty_level == difficulty_level)
        
        # 语言过滤
        if language:
            base_query = base_query.filter(Template.language == language)
        
        # 特色模板过滤
        if is_featured is not None:
            base_query = base_query.filter(Template.is_featured == is_featured)
        
        # 认证模板过滤
        if is_verified is not None:
            base_query = base_query.filter(Template.is_verified == is_verified)
        
        # 创建者过滤
        if creator_id:
            base_query = base_query.filter(Template.creator_id == creator_id)
        
        # 总数查询
        total = base_query.count()
        
        # 排序
        if sort_by == "rating":
            order_column = Template.rating
        elif sort_by == "usage_count":
            order_column = Template.usage_count
        elif sort_by == "created_at":
            order_column = Template.created_at
        elif sort_by == "updated_at":
            order_column = Template.updated_at
        elif sort_by == "name":
            order_column = Template.name
        else:
            order_column = Template.created_at
        
        if sort_order == "asc":
            base_query = base_query.order_by(asc(order_column))
        else:
            base_query = base_query.order_by(desc(order_column))
        
        # 分页
        offset = (page - 1) * page_size
        templates = base_query.offset(offset).limit(page_size).all()
        
        return templates, total
    
    async def get_popular_templates(self, limit: int = 10) -> List[Template]:
        """获取热门模板"""
        return self.db.query(Template).filter(
            Template.is_public == True
        ).order_by(
            desc(Template.usage_count),
            desc(Template.rating)
        ).limit(limit).all()
    
    async def get_featured_templates(self, limit: int = 10) -> List[Template]:
        """获取推荐模板"""
        return self.db.query(Template).filter(
            and_(
                Template.is_public == True,
                Template.is_featured == True
            )
        ).order_by(desc(Template.created_at)).limit(limit).all()
    
    async def get_recent_templates(self, limit: int = 10) -> List[Template]:
        """获取最新模板"""
        return self.db.query(Template).filter(
            Template.is_public == True
        ).order_by(desc(Template.created_at)).limit(limit).all()
    
    async def use_template(self, template_id: str, user_id: str) -> bool:
        """使用模板（记录使用统计）"""
        try:
            # 记录使用记录
            usage = TemplateUsage(
                template_id=template_id,
                user_id=user_id
            )
            self.db.add(usage)
            
            # 更新使用计数
            template = self.db.query(Template).filter(Template.id == template_id).first()
            if template:
                template.usage_count += 1
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            return False
    
    async def rate_template(
        self,
        template_id: str,
        user_id: str,
        rating: int,
        comment: str = None
    ) -> bool:
        """评分模板"""
        if not (1 <= rating <= 5):
            raise ValueError("评分必须在1-5之间")
        
        try:
            # 检查是否已经评分
            existing_rating = self.db.query(TemplateRating).filter(
                and_(
                    TemplateRating.template_id == template_id,
                    TemplateRating.user_id == user_id
                )
            ).first()
            
            if existing_rating:
                # 更新评分
                existing_rating.rating = rating
                existing_rating.comment = comment
                existing_rating.updated_at = datetime.utcnow()
            else:
                # 新增评分
                new_rating = TemplateRating(
                    template_id=template_id,
                    user_id=user_id,
                    rating=rating,
                    comment=comment
                )
                self.db.add(new_rating)
            
            # 重新计算平均评分
            await self._recalculate_template_rating(template_id)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"评分失败: {str(e)}")
    
    async def _recalculate_template_rating(self, template_id: str):
        """重新计算模板平均评分"""
        result = self.db.query(
            func.avg(TemplateRating.rating).label('avg_rating'),
            func.count(TemplateRating.rating).label('rating_count')
        ).filter(TemplateRating.template_id == template_id).first()
        
        template = self.db.query(Template).filter(Template.id == template_id).first()
        if template and result:
            template.rating = result.avg_rating or 0.0
            template.rating_count = result.rating_count or 0
    
    async def _update_tag_usage(self, tags: List[str]):
        """更新标签使用统计"""
        for tag_name in tags:
            tag = self.db.query(TemplateTag).filter(TemplateTag.name == tag_name).first()
            if tag:
                tag.usage_count += 1
            else:
                # 创建新标签
                new_tag = TemplateTag(name=tag_name, usage_count=1)
                self.db.add(new_tag)


def get_template_service(db: Session) -> TemplateService:
    """获取模板服务实例"""
    return TemplateService(db)
