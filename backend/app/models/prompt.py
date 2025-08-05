"""
提示词相关数据模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from config.database import Base

class Prompt(Base):
    """提示词模型"""
    __tablename__ = "prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    tags = Column(ARRAY(String), default=[])
    is_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="prompts")
    analysis_results = relationship("AnalysisResult", back_populates="prompt")

    def __repr__(self):
        return f"<Prompt(id={self.id}, title={self.title}, user_id={self.user_id})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "is_template": self.is_template,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class AnalysisResult(Base):
    """分析结果模型"""
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Integer, nullable=False)  # 0-100
    semantic_clarity = Column(Integer, nullable=False)  # 0-100
    structural_integrity = Column(Integer, nullable=False)  # 0-100
    logical_coherence = Column(Integer, nullable=False)  # 0-100
    analysis_details = Column(JSONB, default={})
    processing_time_ms = Column(Integer, nullable=True)
    ai_model_used = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    prompt = relationship("Prompt", back_populates="analysis_results")
    suggestions = relationship("OptimizationSuggestion", back_populates="analysis")

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, prompt_id={self.prompt_id}, score={self.overall_score})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "prompt_id": str(self.prompt_id),
            "overall_score": self.overall_score,
            "semantic_clarity": self.semantic_clarity,
            "structural_integrity": self.structural_integrity,
            "logical_coherence": self.logical_coherence,
            "analysis_details": self.analysis_details,
            "processing_time_ms": self.processing_time_ms,
            "ai_model_used": self.ai_model_used,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class OptimizationSuggestion(Base):
    """优化建议模型"""
    __tablename__ = "optimization_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False)
    suggestion_type = Column(String(50), nullable=False)
    priority = Column(Integer, nullable=False)  # 1-5, 1最高
    description = Column(Text, nullable=False)
    improvement_plan = Column(Text, nullable=True)
    expected_impact = Column(String(20), nullable=True)  # low, medium, high
    is_applied = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    analysis = relationship("AnalysisResult", back_populates="suggestions")

    def __repr__(self):
        return f"<OptimizationSuggestion(id={self.id}, type={self.suggestion_type}, priority={self.priority})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "analysis_id": str(self.analysis_id),
            "suggestion_type": self.suggestion_type,
            "priority": self.priority,
            "description": self.description,
            "improvement_plan": self.improvement_plan,
            "expected_impact": self.expected_impact,
            "is_applied": self.is_applied,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
