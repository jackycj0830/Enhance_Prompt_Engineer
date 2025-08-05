"""
优化建议生成引擎 - 智能建议算法和个性化推荐
"""

import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

from .ai_client import AIClient, AIResponse, AIClientError
from .prompt_analyzer import DetailedAnalysis, AnalysisMetrics

class SuggestionType(Enum):
    """建议类型枚举"""
    CLARITY = "clarity"           # 清晰度改进
    STRUCTURE = "structure"       # 结构优化
    SPECIFICITY = "specificity"   # 具体性增强
    CONTEXT = "context"          # 上下文补充
    FORMAT = "format"            # 格式规范
    ROLE = "role"               # 角色定义
    EXAMPLES = "examples"        # 示例添加
    CONSTRAINTS = "constraints"   # 约束条件

class Priority(Enum):
    """优先级枚举"""
    CRITICAL = 1    # 关键问题
    HIGH = 2        # 高优先级
    MEDIUM = 3      # 中等优先级
    LOW = 4         # 低优先级
    OPTIONAL = 5    # 可选优化

class Impact(Enum):
    """影响程度枚举"""
    HIGH = "high"       # 高影响
    MEDIUM = "medium"   # 中等影响
    LOW = "low"         # 低影响

@dataclass
class OptimizationSuggestion:
    """优化建议数据结构"""
    id: str
    type: SuggestionType
    priority: Priority
    impact: Impact
    title: str
    description: str
    improvement_plan: str
    expected_improvement: Dict[str, int]  # 预期各维度改进分数
    examples: List[str]
    reasoning: str
    confidence: float  # 建议的置信度 0-1

@dataclass
class OptimizationResult:
    """优化结果数据结构"""
    original_analysis: DetailedAnalysis
    suggestions: List[OptimizationSuggestion]
    personalized_recommendations: List[str]
    improvement_roadmap: List[str]
    estimated_score_improvement: int
    processing_time: float
    model_used: str

class OptimizationEngine:
    """优化建议生成引擎"""
    
    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client
        
        # 建议生成系统提示词
        self.suggestion_system_prompt = """你是一个专业的提示词工程师和优化专家。基于提供的分析结果，生成具体、可操作的优化建议。

请为每个建议提供：
1. 建议类型（clarity/structure/specificity/context/format/role/examples/constraints）
2. 优先级（1-5，1最高）
3. 影响程度（high/medium/low）
4. 标题和详细描述
5. 具体的改进计划
6. 预期的改进效果
7. 示例说明
8. 推理过程

请以JSON格式返回建议列表，确保建议具体、可操作且有针对性。"""

        # 个性化推荐系统提示词
        self.personalization_system_prompt = """基于用户的使用场景和偏好，提供个性化的提示词优化建议。

考虑因素：
- 用户的AI模型偏好
- 使用场景（创作、编程、分析等）
- 历史优化效果
- 个人写作风格

提供3-5条个性化建议，每条建议应该简洁明了且针对性强。"""

    def analyze_weaknesses(self, analysis: DetailedAnalysis) -> List[Tuple[str, int, str]]:
        """分析提示词的主要弱点"""
        weaknesses = []
        metrics = analysis.metrics
        
        # 检查各维度评分，识别需要改进的方面
        if metrics.semantic_clarity < 70:
            severity = 1 if metrics.semantic_clarity < 50 else 2
            weaknesses.append(("semantic_clarity", severity, "语义表达不够清晰明确"))
        
        if metrics.structural_integrity < 70:
            severity = 1 if metrics.structural_integrity < 50 else 2
            weaknesses.append(("structural_integrity", severity, "结构组织需要优化"))
        
        if metrics.logical_coherence < 70:
            severity = 1 if metrics.logical_coherence < 50 else 2
            weaknesses.append(("logical_coherence", severity, "逻辑连贯性有待提升"))
        
        if metrics.specificity_score < 70:
            severity = 1 if metrics.specificity_score < 50 else 2
            weaknesses.append(("specificity_score", severity, "指令不够具体明确"))
        
        if metrics.instruction_clarity < 70:
            severity = 1 if metrics.instruction_clarity < 50 else 2
            weaknesses.append(("instruction_clarity", severity, "指令清晰度需要改进"))
        
        if metrics.context_completeness < 70:
            severity = 1 if metrics.context_completeness < 50 else 2
            weaknesses.append(("context_completeness", severity, "上下文信息不够完整"))
        
        # 按严重程度排序
        weaknesses.sort(key=lambda x: x[1])
        return weaknesses

    def generate_rule_based_suggestions(self, analysis: DetailedAnalysis) -> List[OptimizationSuggestion]:
        """基于规则生成优化建议"""
        suggestions = []
        weaknesses = self.analyze_weaknesses(analysis)
        metrics = analysis.metrics
        details = analysis.analysis_details
        
        suggestion_id = 0
        
        for weakness_type, severity, description in weaknesses:
            suggestion_id += 1
            
            if weakness_type == "semantic_clarity":
                suggestions.append(OptimizationSuggestion(
                    id=f"rule_{suggestion_id}",
                    type=SuggestionType.CLARITY,
                    priority=Priority.CRITICAL if severity == 1 else Priority.HIGH,
                    impact=Impact.HIGH,
                    title="提升语义清晰度",
                    description="使用更精确、具体的词汇，避免模糊表达",
                    improvement_plan="1. 替换模糊词汇（如'一些'、'很多'）为具体数量\n2. 使用专业术语替代通用词汇\n3. 明确指定期望的输出类型和格式",
                    expected_improvement={"semantic_clarity": 15, "overall_score": 8},
                    examples=[
                        "模糊：'写一些关于AI的内容'",
                        "清晰：'写3个关于AI在医疗领域应用的具体案例，每个案例200字'"
                    ],
                    reasoning="语义清晰度低会导致AI理解偏差，影响输出质量",
                    confidence=0.9
                ))
            
            elif weakness_type == "structural_integrity":
                suggestions.append(OptimizationSuggestion(
                    id=f"rule_{suggestion_id}",
                    type=SuggestionType.STRUCTURE,
                    priority=Priority.HIGH,
                    impact=Impact.MEDIUM,
                    title="优化结构组织",
                    description="改进提示词的逻辑结构和信息组织方式",
                    improvement_plan="1. 使用编号或分点列出要求\n2. 按逻辑顺序组织信息\n3. 分离背景信息和具体指令",
                    expected_improvement={"structural_integrity": 20, "logical_coherence": 10},
                    examples=[
                        "优化前：混合的长段落描述",
                        "优化后：1. 背景 2. 任务 3. 要求 4. 输出格式"
                    ],
                    reasoning="良好的结构有助于AI理解任务层次和优先级",
                    confidence=0.85
                ))
            
            elif weakness_type == "specificity_score":
                suggestions.append(OptimizationSuggestion(
                    id=f"rule_{suggestion_id}",
                    type=SuggestionType.SPECIFICITY,
                    priority=Priority.CRITICAL,
                    impact=Impact.HIGH,
                    title="增强指令具体性",
                    description="提供更具体、明确的指令和要求",
                    improvement_plan="1. 指定具体的数量、长度、格式\n2. 提供详细的质量标准\n3. 明确约束条件和限制",
                    expected_improvement={"specificity_score": 25, "instruction_clarity": 15},
                    examples=[
                        "模糊：'写得好一点'",
                        "具体：'使用专业术语，控制在500字以内，包含3个要点'"
                    ],
                    reasoning="具体的指令能显著提高输出的准确性和相关性",
                    confidence=0.95
                ))
            
            elif weakness_type == "context_completeness":
                suggestions.append(OptimizationSuggestion(
                    id=f"rule_{suggestion_id}",
                    type=SuggestionType.CONTEXT,
                    priority=Priority.MEDIUM,
                    impact=Impact.MEDIUM,
                    title="补充上下文信息",
                    description="提供更完整的背景信息和上下文",
                    improvement_plan="1. 添加任务背景和目标\n2. 说明目标受众和使用场景\n3. 提供相关的参考信息",
                    expected_improvement={"context_completeness": 20, "overall_score": 10},
                    examples=[
                        "缺少上下文：'翻译这段文字'",
                        "完整上下文：'为技术文档翻译这段英文，目标读者是中国的软件工程师'"
                    ],
                    reasoning="充分的上下文帮助AI生成更符合预期的内容",
                    confidence=0.8
                ))
        
        # 添加通用建议
        basic_metrics = details.get('basic_metrics', {})
        
        # 如果没有示例，建议添加
        if not basic_metrics.get('structural_elements', {}).get('has_examples', False):
            suggestion_id += 1
            suggestions.append(OptimizationSuggestion(
                id=f"rule_{suggestion_id}",
                type=SuggestionType.EXAMPLES,
                priority=Priority.MEDIUM,
                impact=Impact.MEDIUM,
                title="添加示例说明",
                description="提供具体示例来说明期望的输出格式",
                improvement_plan="1. 添加1-2个输出示例\n2. 展示理想的格式和风格\n3. 说明示例的关键特征",
                expected_improvement={"instruction_clarity": 15, "overall_score": 8},
                examples=[
                    "添加示例：'例如：标题：AI的未来\\n内容：人工智能技术正在...'"
                ],
                reasoning="示例能直观展示期望输出，减少理解偏差",
                confidence=0.75
            ))
        
        # 如果没有角色定义，建议添加
        if not any(indicator in analysis.analysis_details.get('basic_metrics', {}).get('word_frequency', {}) 
                  for indicator in ['you', 'act', 'role', '你', '扮演', '角色']):
            suggestion_id += 1
            suggestions.append(OptimizationSuggestion(
                id=f"rule_{suggestion_id}",
                type=SuggestionType.ROLE,
                priority=Priority.LOW,
                impact=Impact.MEDIUM,
                title="定义AI角色",
                description="明确指定AI应该扮演的角色和专业身份",
                improvement_plan="1. 在开头定义AI的角色\n2. 指定相关的专业背景\n3. 说明角色的能力和限制",
                expected_improvement={"instruction_clarity": 10, "context_completeness": 10},
                examples=[
                    "角色定义：'你是一个资深的技术写作专家，擅长将复杂概念简化表达'"
                ],
                reasoning="明确的角色定义有助于AI采用合适的语调和视角",
                confidence=0.7
            ))
        
        return suggestions[:5]  # 最多返回5个建议

    async def generate_ai_suggestions(
        self, 
        analysis: DetailedAnalysis, 
        model: str = "gpt-3.5-turbo"
    ) -> List[OptimizationSuggestion]:
        """使用AI生成优化建议"""
        try:
            # 构建分析摘要
            analysis_summary = {
                "overall_score": analysis.metrics.overall_score,
                "dimensions": {
                    "semantic_clarity": analysis.metrics.semantic_clarity,
                    "structural_integrity": analysis.metrics.structural_integrity,
                    "logical_coherence": analysis.metrics.logical_coherence,
                    "specificity_score": analysis.metrics.specificity_score,
                    "instruction_clarity": analysis.metrics.instruction_clarity,
                    "context_completeness": analysis.metrics.context_completeness
                },
                "strengths": analysis.strengths,
                "weaknesses": analysis.weaknesses,
                "basic_metrics": analysis.analysis_details.get('basic_metrics', {})
            }
            
            prompt = f"""请基于以下提示词分析结果生成优化建议：

分析结果：
{json.dumps(analysis_summary, ensure_ascii=False, indent=2)}

请生成3-5个具体的优化建议，每个建议包含：
- type: 建议类型
- priority: 优先级(1-5)
- impact: 影响程度(high/medium/low)
- title: 建议标题
- description: 详细描述
- improvement_plan: 改进计划
- expected_improvement: 预期改进效果
- examples: 示例说明
- reasoning: 推理过程
- confidence: 置信度(0-1)

请确保建议具体可操作，并以JSON格式返回。"""

            response = await self.ai_client.generate_completion(
                prompt=prompt,
                system_prompt=self.suggestion_system_prompt,
                model=model,
                temperature=0.3
            )
            
            # 解析AI响应
            try:
                ai_suggestions = json.loads(response.content)
                suggestions = []
                
                for i, sugg in enumerate(ai_suggestions.get('suggestions', ai_suggestions)[:5]):
                    suggestions.append(OptimizationSuggestion(
                        id=f"ai_{i+1}",
                        type=SuggestionType(sugg.get('type', 'clarity')),
                        priority=Priority(sugg.get('priority', 3)),
                        impact=Impact(sugg.get('impact', 'medium')),
                        title=sugg.get('title', '优化建议'),
                        description=sugg.get('description', ''),
                        improvement_plan=sugg.get('improvement_plan', ''),
                        expected_improvement=sugg.get('expected_improvement', {}),
                        examples=sugg.get('examples', []),
                        reasoning=sugg.get('reasoning', ''),
                        confidence=float(sugg.get('confidence', 0.8))
                    ))
                
                return suggestions
            
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"AI建议解析失败: {e}")
                return []
        
        except AIClientError as e:
            print(f"AI建议生成失败: {e}")
            return []

    async def generate_personalized_recommendations(
        self,
        analysis: DetailedAnalysis,
        user_preferences: Dict[str, Any],
        model: str = "gpt-3.5-turbo"
    ) -> List[str]:
        """生成个性化推荐"""
        try:
            context = f"""用户偏好：
- 首选AI模型: {user_preferences.get('preferred_ai_model', 'gpt-3.5-turbo')}
- 分析深度: {user_preferences.get('analysis_depth', 'standard')}
- 使用场景: {user_preferences.get('use_case', '通用')}

当前提示词分析结果：
- 总体评分: {analysis.metrics.overall_score}/100
- 主要优点: {', '.join(analysis.strengths[:3])}
- 主要缺点: {', '.join(analysis.weaknesses[:3])}

请提供3-5条个性化的优化建议，考虑用户的偏好和使用场景。"""

            response = await self.ai_client.generate_completion(
                prompt=context,
                system_prompt=self.personalization_system_prompt,
                model=model,
                temperature=0.5
            )
            
            # 简单解析响应为建议列表
            recommendations = []
            lines = response.content.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    recommendations.append(line.lstrip('-•0123456789. '))
            
            return recommendations[:5]
        
        except Exception as e:
            print(f"个性化推荐生成失败: {e}")
            return [
                "建议根据您的使用场景调整提示词风格",
                "考虑使用您偏好的AI模型特性优化指令",
                "根据历史效果调整优化策略"
            ]

    def create_improvement_roadmap(self, suggestions: List[OptimizationSuggestion]) -> List[str]:
        """创建改进路线图"""
        # 按优先级排序建议
        sorted_suggestions = sorted(suggestions, key=lambda x: x.priority.value)
        
        roadmap = []
        roadmap.append("🎯 立即执行（关键问题）:")
        critical_high = [s for s in sorted_suggestions if s.priority.value <= 2]
        for sugg in critical_high:
            roadmap.append(f"   • {sugg.title}")
        
        roadmap.append("\n📈 短期优化（1-2天内）:")
        medium = [s for s in sorted_suggestions if s.priority.value == 3]
        for sugg in medium:
            roadmap.append(f"   • {sugg.title}")
        
        roadmap.append("\n🔧 长期完善（可选）:")
        low_optional = [s for s in sorted_suggestions if s.priority.value >= 4]
        for sugg in low_optional:
            roadmap.append(f"   • {sugg.title}")
        
        return roadmap

    async def generate_optimization_result(
        self,
        analysis: DetailedAnalysis,
        user_preferences: Dict[str, Any] = None,
        model: str = "gpt-3.5-turbo",
        use_ai_suggestions: bool = True
    ) -> OptimizationResult:
        """生成完整的优化结果"""
        import time
        start_time = time.time()
        
        # 生成基于规则的建议
        rule_suggestions = self.generate_rule_based_suggestions(analysis)
        
        # 生成AI建议（如果启用）
        ai_suggestions = []
        if use_ai_suggestions and self.ai_client.get_available_models():
            ai_suggestions = await self.generate_ai_suggestions(analysis, model)
        
        # 合并建议，去重并排序
        all_suggestions = rule_suggestions + ai_suggestions
        # 简单去重：基于标题
        seen_titles = set()
        unique_suggestions = []
        for sugg in all_suggestions:
            if sugg.title not in seen_titles:
                unique_suggestions.append(sugg)
                seen_titles.add(sugg.title)
        
        # 按优先级排序
        unique_suggestions.sort(key=lambda x: (x.priority.value, -x.confidence))
        
        # 生成个性化推荐
        personalized_recommendations = []
        if user_preferences and self.ai_client.get_available_models():
            personalized_recommendations = await self.generate_personalized_recommendations(
                analysis, user_preferences, model
            )
        
        # 创建改进路线图
        improvement_roadmap = self.create_improvement_roadmap(unique_suggestions)
        
        # 估算总体改进分数
        estimated_improvement = sum(
            sugg.expected_improvement.get('overall_score', 0) 
            for sugg in unique_suggestions[:3]  # 只考虑前3个建议
        )
        
        processing_time = time.time() - start_time
        
        return OptimizationResult(
            original_analysis=analysis,
            suggestions=unique_suggestions[:5],  # 最多返回5个建议
            personalized_recommendations=personalized_recommendations,
            improvement_roadmap=improvement_roadmap,
            estimated_score_improvement=min(estimated_improvement, 30),  # 最大改进30分
            processing_time=processing_time,
            model_used=model if use_ai_suggestions else "rule-based"
        )

# 全局优化引擎实例
_optimization_engine = None

def get_optimization_engine(ai_client: AIClient) -> OptimizationEngine:
    """获取优化引擎实例"""
    global _optimization_engine
    if _optimization_engine is None:
        _optimization_engine = OptimizationEngine(ai_client)
    return _optimization_engine
