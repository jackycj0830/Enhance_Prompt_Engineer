"""
数据模型包
"""

from .user import User, UserPreference
from .prompt import Prompt, AnalysisResult, OptimizationSuggestion
from .template import Template

__all__ = [
    "User",
    "UserPreference", 
    "Prompt",
    "AnalysisResult",
    "OptimizationSuggestion",
    "Template"
]
