"""
提示词分析服务 - 多维度分析算法
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

from .ai_client import AIClient, AIResponse, AIClientError

# 下载必要的NLTK数据
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

@dataclass
class AnalysisMetrics:
    """分析指标数据结构"""
    overall_score: int
    semantic_clarity: int
    structural_integrity: int
    logical_coherence: int
    specificity_score: int
    complexity_score: float
    readability_score: int
    instruction_clarity: int
    context_completeness: int

@dataclass
class DetailedAnalysis:
    """详细分析结果"""
    metrics: AnalysisMetrics
    analysis_details: Dict[str, Any]
    suggestions: List[str]
    strengths: List[str]
    weaknesses: List[str]
    processing_time: float
    model_used: str

class PromptAnalyzer:
    """提示词分析器"""
    
    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.stop_words = set(stopwords.words('english'))
        
        # 分析提示词模板
        self.analysis_system_prompt = """你是一个专业的提示词工程师和分析专家。请对给定的提示词进行全面的质量分析。

请从以下维度进行评估（每个维度0-100分）：

1. 语义清晰度 (Semantic Clarity): 提示词的意思是否明确、无歧义
2. 结构完整性 (Structural Integrity): 提示词的组织结构是否合理、完整
3. 逻辑连贯性 (Logical Coherence): 指令之间是否逻辑清晰、连贯
4. 具体性程度 (Specificity): 指令是否具体、明确，避免模糊表达
5. 指令清晰度 (Instruction Clarity): 期望的输出和行为是否明确
6. 上下文完整性 (Context Completeness): 是否提供了足够的背景信息

请以JSON格式返回分析结果，包含：
- scores: 各维度评分
- strengths: 优点列表
- weaknesses: 缺点列表
- suggestions: 改进建议列表
- analysis_details: 详细分析说明

确保返回有效的JSON格式。"""

    def calculate_basic_metrics(self, text: str) -> Dict[str, Any]:
        """计算基础文本指标"""
        # 基础统计
        word_count = len(text.split())
        char_count = len(text)
        sentence_count = len(sent_tokenize(text))
        
        # 复杂度分析
        avg_word_length = np.mean([len(word) for word in text.split()])
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # 可读性评分（简化版Flesch Reading Ease）
        if sentence_count > 0 and word_count > 0:
            readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length / word_count * 100)
            readability = max(0, min(100, readability))
        else:
            readability = 50
        
        # 情感分析
        sentiment_scores = self.sentiment_analyzer.polarity_scores(text)
        
        # 关键词密度
        words = [word.lower() for word in word_tokenize(text) if word.isalpha()]
        word_freq = {}
        for word in words:
            if word not in self.stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 结构分析
        has_questions = '?' in text
        has_examples = any(keyword in text.lower() for keyword in ['example', 'for instance', 'such as', '例如', '比如'])
        has_constraints = any(keyword in text.lower() for keyword in ['must', 'should', 'required', '必须', '应该', '要求'])
        has_format_spec = any(keyword in text.lower() for keyword in ['format', 'structure', 'json', 'xml', '格式', '结构'])
        
        return {
            'word_count': word_count,
            'char_count': char_count,
            'sentence_count': sentence_count,
            'avg_word_length': round(avg_word_length, 2),
            'avg_sentence_length': round(avg_sentence_length, 2),
            'readability_score': round(readability),
            'sentiment_scores': sentiment_scores,
            'word_frequency': dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
            'structural_elements': {
                'has_questions': has_questions,
                'has_examples': has_examples,
                'has_constraints': has_constraints,
                'has_format_specification': has_format_spec
            }
        }
    
    def calculate_specificity_score(self, text: str) -> int:
        """计算具体性评分"""
        # 模糊词汇检测
        vague_words = [
            'some', 'many', 'few', 'several', 'various', 'different', 'good', 'bad', 'nice', 'great',
            '一些', '很多', '少数', '各种', '不同', '好的', '坏的', '不错', '很好'
        ]
        
        # 具体性指标词汇
        specific_indicators = [
            'exactly', 'precisely', 'specifically', 'detailed', 'step-by-step', 'format',
            '确切', '精确', '具体', '详细', '逐步', '格式'
        ]
        
        text_lower = text.lower()
        vague_count = sum(1 for word in vague_words if word in text_lower)
        specific_count = sum(1 for word in specific_indicators if word in text_lower)
        
        # 数字和具体值的存在
        has_numbers = bool(re.search(r'\d+', text))
        has_quotes = '"' in text or "'" in text
        has_brackets = '[' in text or '(' in text
        
        # 计算评分
        base_score = 50
        base_score += specific_count * 10
        base_score -= vague_count * 5
        base_score += 10 if has_numbers else 0
        base_score += 5 if has_quotes else 0
        base_score += 5 if has_brackets else 0
        
        return max(0, min(100, base_score))
    
    def calculate_instruction_clarity(self, text: str) -> int:
        """计算指令清晰度"""
        # 指令词汇检测
        instruction_words = [
            'write', 'create', 'generate', 'analyze', 'explain', 'describe', 'list', 'compare',
            'summarize', 'translate', 'convert', 'format', 'extract', 'identify',
            '写', '创建', '生成', '分析', '解释', '描述', '列出', '比较', '总结', '翻译', '转换', '格式化', '提取', '识别'
        ]
        
        text_lower = text.lower()
        instruction_count = sum(1 for word in instruction_words if word in text_lower)
        
        # 角色定义检测
        role_indicators = [
            'you are', 'act as', 'pretend to be', 'imagine you are', 'as a',
            '你是', '扮演', '假设你是', '作为一个'
        ]
        has_role = any(indicator in text_lower for indicator in role_indicators)
        
        # 输出格式要求
        output_indicators = [
            'output', 'result', 'response', 'answer', 'format', 'structure',
            '输出', '结果', '回答', '格式', '结构'
        ]
        has_output_spec = any(indicator in text_lower for indicator in output_indicators)
        
        # 计算评分
        base_score = 40
        base_score += instruction_count * 8
        base_score += 15 if has_role else 0
        base_score += 15 if has_output_spec else 0
        
        return max(0, min(100, base_score))
    
    async def ai_analysis(self, text: str, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """使用AI进行深度分析"""
        try:
            response = await self.ai_client.generate_completion(
                prompt=f"请分析以下提示词：\n\n{text}",
                system_prompt=self.analysis_system_prompt,
                model=model,
                temperature=0.3
            )
            
            # 尝试解析JSON响应
            try:
                analysis_result = json.loads(response.content)
                return {
                    'ai_analysis': analysis_result,
                    'model_used': model,
                    'response_time': response.response_time,
                    'token_usage': response.usage
                }
            except json.JSONDecodeError:
                # 如果不是有效JSON，返回原始文本
                return {
                    'ai_analysis': {'raw_response': response.content},
                    'model_used': model,
                    'response_time': response.response_time,
                    'token_usage': response.usage
                }
        
        except AIClientError as e:
            return {
                'ai_analysis': {'error': str(e)},
                'model_used': model,
                'response_time': 0,
                'token_usage': {'total_tokens': 0}
            }
    
    async def analyze_prompt(
        self, 
        text: str, 
        model: str = "gpt-3.5-turbo",
        use_ai_analysis: bool = True
    ) -> DetailedAnalysis:
        """完整的提示词分析"""
        import time
        start_time = time.time()
        
        # 基础指标计算
        basic_metrics = self.calculate_basic_metrics(text)
        specificity_score = self.calculate_specificity_score(text)
        instruction_clarity = self.calculate_instruction_clarity(text)
        
        # AI深度分析（如果启用）
        ai_result = {}
        if use_ai_analysis and self.ai_client.get_available_models():
            ai_result = await self.ai_analysis(text, model)
        
        # 综合评分计算
        readability = basic_metrics['readability_score']
        
        # 从AI分析中提取评分（如果可用）
        ai_scores = {}
        if 'ai_analysis' in ai_result and 'scores' in ai_result['ai_analysis']:
            ai_scores = ai_result['ai_analysis']['scores']
        
        # 计算各维度评分
        semantic_clarity = ai_scores.get('semantic_clarity', 
            min(100, max(0, readability + (10 if basic_metrics['structural_elements']['has_examples'] else 0))))
        
        structural_integrity = ai_scores.get('structural_integrity',
            min(100, max(0, 60 + sum([
                10 if basic_metrics['structural_elements']['has_questions'] else 0,
                10 if basic_metrics['structural_elements']['has_examples'] else 0,
                10 if basic_metrics['structural_elements']['has_constraints'] else 0,
                10 if basic_metrics['structural_elements']['has_format_specification'] else 0
            ]))))
        
        logical_coherence = ai_scores.get('logical_coherence',
            min(100, max(0, 70 + (basic_metrics['sentence_count'] * 2) - (abs(basic_metrics['sentiment_scores']['compound']) * 10))))
        
        context_completeness = ai_scores.get('context_completeness',
            min(100, max(0, 50 + (basic_metrics['word_count'] // 10))))
        
        # 计算总体评分
        overall_score = int(np.mean([
            semantic_clarity,
            structural_integrity, 
            logical_coherence,
            specificity_score,
            instruction_clarity,
            context_completeness
        ]))
        
        # 构建分析指标
        metrics = AnalysisMetrics(
            overall_score=overall_score,
            semantic_clarity=semantic_clarity,
            structural_integrity=structural_integrity,
            logical_coherence=logical_coherence,
            specificity_score=specificity_score,
            complexity_score=round(basic_metrics['avg_sentence_length'], 2),
            readability_score=readability,
            instruction_clarity=instruction_clarity,
            context_completeness=context_completeness
        )
        
        # 构建详细分析结果
        analysis_details = {
            'basic_metrics': basic_metrics,
            'token_count': self.ai_client.count_tokens(text, model) if self.ai_client.get_available_models() else len(text.split()),
            'ai_analysis_result': ai_result.get('ai_analysis', {}),
            'model_performance': {
                'model_used': ai_result.get('model_used', 'rule-based'),
                'response_time': ai_result.get('response_time', 0),
                'token_usage': ai_result.get('token_usage', {})
            }
        }
        
        # 提取优缺点和建议
        strengths = ai_result.get('ai_analysis', {}).get('strengths', [])
        weaknesses = ai_result.get('ai_analysis', {}).get('weaknesses', [])
        suggestions = ai_result.get('ai_analysis', {}).get('suggestions', [])
        
        # 如果AI分析不可用，使用规则生成
        if not strengths:
            strengths = self._generate_rule_based_strengths(basic_metrics, metrics)
        if not weaknesses:
            weaknesses = self._generate_rule_based_weaknesses(basic_metrics, metrics)
        if not suggestions:
            suggestions = self._generate_rule_based_suggestions(basic_metrics, metrics)
        
        processing_time = time.time() - start_time
        
        return DetailedAnalysis(
            metrics=metrics,
            analysis_details=analysis_details,
            suggestions=suggestions,
            strengths=strengths,
            weaknesses=weaknesses,
            processing_time=processing_time,
            model_used=ai_result.get('model_used', 'rule-based')
        )
    
    def _generate_rule_based_strengths(self, basic_metrics: Dict, metrics: AnalysisMetrics) -> List[str]:
        """基于规则生成优点"""
        strengths = []
        
        if metrics.readability_score > 70:
            strengths.append("文本可读性良好，易于理解")
        
        if basic_metrics['structural_elements']['has_examples']:
            strengths.append("包含示例，有助于理解期望输出")
        
        if basic_metrics['structural_elements']['has_constraints']:
            strengths.append("明确指定了约束条件")
        
        if metrics.specificity_score > 70:
            strengths.append("指令具体明确，避免了模糊表达")
        
        if basic_metrics['word_count'] > 50:
            strengths.append("提供了充分的上下文信息")
        
        return strengths
    
    def _generate_rule_based_weaknesses(self, basic_metrics: Dict, metrics: AnalysisMetrics) -> List[str]:
        """基于规则生成缺点"""
        weaknesses = []
        
        if metrics.readability_score < 50:
            weaknesses.append("文本可读性较差，可能难以理解")
        
        if not basic_metrics['structural_elements']['has_examples']:
            weaknesses.append("缺少示例，可能导致输出不符合预期")
        
        if metrics.specificity_score < 50:
            weaknesses.append("指令过于模糊，需要更具体的描述")
        
        if basic_metrics['word_count'] < 20:
            weaknesses.append("上下文信息不足，可能影响输出质量")
        
        if metrics.instruction_clarity < 60:
            weaknesses.append("指令不够清晰，需要明确期望的行为")
        
        return weaknesses
    
    def _generate_rule_based_suggestions(self, basic_metrics: Dict, metrics: AnalysisMetrics) -> List[str]:
        """基于规则生成建议"""
        suggestions = []
        
        if metrics.specificity_score < 70:
            suggestions.append("使用更具体的词汇，避免'一些'、'很多'等模糊表达")
        
        if not basic_metrics['structural_elements']['has_examples']:
            suggestions.append("添加具体示例来说明期望的输出格式")
        
        if metrics.instruction_clarity < 70:
            suggestions.append("明确指定AI应该扮演的角色和执行的任务")
        
        if not basic_metrics['structural_elements']['has_format_specification']:
            suggestions.append("指定输出格式（如JSON、列表、段落等）")
        
        if basic_metrics['sentence_count'] == 1:
            suggestions.append("将长句拆分为多个短句，提高可读性")
        
        return suggestions

# 全局分析器实例
_analyzer_instance = None

def get_prompt_analyzer(ai_client: AIClient) -> PromptAnalyzer:
    """获取提示词分析器实例"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = PromptAnalyzer(ai_client)
    return _analyzer_instance
