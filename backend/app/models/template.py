"""
模板相关数据模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from config.database import Base

class Template(Base):
    """模板模型"""
    __tablename__ = "templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    tags = Column(ARRAY(String), default=[])
    usage_count = Column(Integer, default=0)
    rating = Column(Numeric(3, 2), default=0.00)  # 0.00-5.00
    rating_count = Column(Integer, default=0)  # 评分人数
    is_featured = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # 官方认证
    difficulty_level = Column(String(20), default="beginner")  # beginner, intermediate, advanced
    language = Column(String(10), default="zh-CN")  # 语言标识
    industry = Column(String(50), nullable=True)  # 行业分类
    use_case = Column(String(100), nullable=True)  # 使用场景
    metadata = Column(JSONB, default={})  # 扩展元数据
    version = Column(String(20), default="1.0.0")  # 版本号
    parent_id = Column(UUID(as_uuid=True), ForeignKey("templates.id", ondelete="SET NULL"), nullable=True)  # 父模板ID（用于版本管理）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    creator = relationship("User", back_populates="templates")
    ratings = relationship("TemplateRating", back_populates="template", cascade="all, delete-orphan")
    usage_records = relationship("TemplateUsage", back_populates="template", cascade="all, delete-orphan")
    collections = relationship("TemplateCollection", back_populates="template", cascade="all, delete-orphan")
    parent = relationship("Template", remote_side=[id], backref="children")

    # 索引
    __table_args__ = (
        Index('idx_template_category', 'category'),
        Index('idx_template_tags', 'tags'),
        Index('idx_template_industry', 'industry'),
        Index('idx_template_difficulty', 'difficulty_level'),
        Index('idx_template_public', 'is_public'),
        Index('idx_template_featured', 'is_featured'),
        Index('idx_template_rating', 'rating'),
        Index('idx_template_usage', 'usage_count'),
    )

    def __repr__(self):
        return f"<Template(id={self.id}, name={self.name}, creator_id={self.creator_id})>"

    def to_dict(self, include_content=True):
        """转换为字典"""
        result = {
            "id": str(self.id),
            "creator_id": str(self.creator_id) if self.creator_id else None,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": self.tags or [],
            "usage_count": self.usage_count,
            "rating": float(self.rating) if self.rating else 0.0,
            "rating_count": self.rating_count,
            "is_featured": self.is_featured,
            "is_public": self.is_public,
            "is_verified": self.is_verified,
            "difficulty_level": self.difficulty_level,
            "language": self.language,
            "industry": self.industry,
            "use_case": self.use_case,
            "metadata": self.metadata or {},
            "version": self.version,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        if include_content:
            result["content"] = self.content

        return result

class TemplateRating(Base):
    """模板评分模型"""
    __tablename__ = "template_ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    template = relationship("Template", back_populates="ratings")
    user = relationship("User")

    def __repr__(self):
        return f"<TemplateRating(template_id={self.template_id}, user_id={self.user_id}, rating={self.rating})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "template_id": str(self.template_id),
            "user_id": str(self.user_id),
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class TemplateUsage(Base):
    """模板使用记录模型"""
    __tablename__ = "template_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    used_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    template = relationship("Template")
    user = relationship("User")

    def __repr__(self):
        return f"<TemplateUsage(template_id={self.template_id}, user_id={self.user_id})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "template_id": str(self.template_id),
            "user_id": str(self.user_id),
            "used_at": self.used_at.isoformat() if self.used_at else None
        }


class TemplateCollection(Base):
    """模板收藏表"""
    __tablename__ = "template_collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    collection_name = Column(String(100), nullable=True)  # 收藏夹名称
    notes = Column(Text, nullable=True)  # 个人备注
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    user = relationship("User")
    template = relationship("Template", back_populates="collections")

    # 索引
    __table_args__ = (
        Index('idx_collection_user', 'user_id'),
        Index('idx_collection_template', 'template_id'),
        Index('idx_collection_name', 'collection_name'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "template_id": str(self.template_id),
            "collection_name": self.collection_name,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class TemplateCategory(Base):
    """模板分类表"""
    __tablename__ = "template_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # 图标名称
    color = Column(String(20), nullable=True)  # 颜色代码
    parent_id = Column(UUID(as_uuid=True), ForeignKey("template_categories.id", ondelete="CASCADE"), nullable=True)
    sort_order = Column(Integer, default=0)  # 排序
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    parent = relationship("TemplateCategory", remote_side=[id], backref="children")

    # 索引
    __table_args__ = (
        Index('idx_category_name', 'name'),
        Index('idx_category_parent', 'parent_id'),
        Index('idx_category_active', 'is_active'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class TemplateTag(Base):
    """模板标签表"""
    __tablename__ = "template_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(20), nullable=True)  # 标签颜色
    usage_count = Column(Integer, default=0)  # 使用次数
    is_featured = Column(Boolean, default=False)  # 是否推荐标签
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 索引
    __table_args__ = (
        Index('idx_tag_name', 'name'),
        Index('idx_tag_usage', 'usage_count'),
        Index('idx_tag_featured', 'is_featured'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "usage_count": self.usage_count,
            "is_featured": self.is_featured,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
