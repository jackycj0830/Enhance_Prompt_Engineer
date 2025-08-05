"""
模板相关数据模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, ARRAY
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
    is_featured = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    creator = relationship("User", back_populates="templates")
    ratings = relationship("TemplateRating", back_populates="template")

    def __repr__(self):
        return f"<Template(id={self.id}, name={self.name}, creator_id={self.creator_id})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "creator_id": str(self.creator_id) if self.creator_id else None,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "rating": float(self.rating) if self.rating else 0.0,
            "is_featured": self.is_featured,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

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
