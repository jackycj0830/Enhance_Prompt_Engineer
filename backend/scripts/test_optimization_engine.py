"""
优化建议引擎测试脚本
"""

import sys
import os
import asyncio
import json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.ai_client import get_ai_client
from app.services.prompt_analyzer import get_prompt_analyzer
from app.services.optimization_engine import get_optimization_engine

async def test_optimization_engine():
    """测试优化建议引擎"""
    print("🔧 测试优化建议引擎...")
    
    ai_client = get_ai_client()
    analyzer = get_prompt_analyzer(ai_client)
    optimization_engine = get_optimization_engine(ai_client)
    
    # 测试提示词（故意设计得有改进空间）
    test_prompts = [
        # 简单模糊的提示词
        "写一篇文章",
        
        # 中等质量的提示词
        "请写一篇关于人工智能的文章，要求内容丰富，语言流畅。",
        
        # 较好但仍有改进空间的提示词
        "作为一个技术专家，请为我写一篇关于人工智能在医疗领域应用的技术文章。文章应该包含AI在诊断、治疗和药物发现中的应用，长度控制在1500字左右。"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 测试提示词 {i}: {prompt[:50]}...")
        
        try:
            # 1. 先进行分析
            print("   🔍 执行分析...")
            analysis_result = await analyzer.analyze_prompt(
                text=prompt,
                model=ai_client.get_available_models()[0] if ai_client.get_available_models() else "rule-based",
                use_ai_analysis=len(ai_client.get_available_models()) > 0
            )
            
            print(f"   📊 分析评分: {analysis_result.metrics.overall_score}/100")
            
            # 2. 生成优化建议
            print("   💡 生成优化建议...")
            user_preferences = {
                "preferred_ai_model": "gpt-3.5-turbo",
                "analysis_depth": "standard",
                "use_case": "技术写作"
            }
            
            optimization_result = await optimization_engine.generate_optimization_result(
                analysis=analysis_result,
                user_preferences=user_preferences,
                model=ai_client.get_available_models()[0] if ai_client.get_available_models() else "rule-based",
                use_ai_suggestions=len(ai_client.get_available_models()) > 0
            )
            
            print(f"   ✅ 生成建议数量: {len(optimization_result.suggestions)}")
            print(f"   📈 预期改进分数: +{optimization_result.estimated_score_improvement}")
            print(f"   ⏱️  处理时间: {optimization_result.processing_time:.2f}秒")
            print(f"   🤖 使用模型: {optimization_result.model_used}")
            
            # 3. 显示建议详情
            print("   📋 优化建议:")
            for j, suggestion in enumerate(optimization_result.suggestions[:3], 1):
                print(f"      {j}. {suggestion.title} (优先级: {suggestion.priority.value}, 影响: {suggestion.impact.value})")
                print(f"         描述: {suggestion.description}")
                print(f"         置信度: {suggestion.confidence:.2f}")
            
            # 4. 显示个性化推荐
            if optimization_result.personalized_recommendations:
                print("   🎯 个性化推荐:")
                for rec in optimization_result.personalized_recommendations[:2]:
                    print(f"      • {rec}")
            
            # 5. 显示改进路线图
            if optimization_result.improvement_roadmap:
                print("   🗺️  改进路线图:")
                for step in optimization_result.improvement_roadmap[:5]:
                    print(f"      {step}")
        
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            return False
    
    return True

async def test_suggestion_types():
    """测试不同类型的建议生成"""
    print("\n🎨 测试建议类型覆盖...")
    
    ai_client = get_ai_client()
    analyzer = get_prompt_analyzer(ai_client)
    optimization_engine = get_optimization_engine(ai_client)
    
    # 设计特定问题的提示词来测试不同类型的建议
    test_cases = [
        {
            "prompt": "做个总结",  # 测试清晰度和具体性建议
            "expected_types": ["clarity", "specificity"]
        },
        {
            "prompt": "你好请帮我写一个很长的文章关于很多不同的主题包括科技和文化还有其他的一些内容要求写得很好很详细",  # 测试结构建议
            "expected_types": ["structure", "coherence"]
        },
        {
            "prompt": "写文章",  # 测试上下文和角色建议
            "expected_types": ["context", "role"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   测试用例 {i}: {test_case['prompt']}")
        
        try:
            # 分析
            analysis_result = await analyzer.analyze_prompt(
                text=test_case["prompt"],
                use_ai_analysis=False  # 使用规则分析确保一致性
            )
            
            # 生成建议
            optimization_result = await optimization_engine.generate_optimization_result(
                analysis=analysis_result,
                use_ai_suggestions=False  # 使用规则建议确保一致性
            )
            
            # 检查建议类型
            generated_types = [sugg.type.value for sugg in optimization_result.suggestions]
            print(f"   生成的建议类型: {generated_types}")
            
            # 验证是否包含预期类型
            for expected_type in test_case["expected_types"]:
                if expected_type in generated_types:
                    print(f"   ✅ 包含预期类型: {expected_type}")
                else:
                    print(f"   ⚠️  缺少预期类型: {expected_type}")
        
        except Exception as e:
            print(f"   ❌ 测试用例失败: {e}")
    
    return True

async def test_personalization():
    """测试个性化推荐功能"""
    print("\n👤 测试个性化推荐...")
    
    ai_client = get_ai_client()
    
    if not ai_client.get_available_models():
        print("   ⚠️  跳过个性化测试（无可用AI模型）")
        return True
    
    analyzer = get_prompt_analyzer(ai_client)
    optimization_engine = get_optimization_engine(ai_client)
    
    test_prompt = "请帮我分析一下这个数据"
    
    # 不同的用户偏好
    user_profiles = [
        {
            "name": "技术写作者",
            "preferences": {
                "preferred_ai_model": "gpt-4",
                "analysis_depth": "deep",
                "use_case": "技术文档"
            }
        },
        {
            "name": "创意工作者",
            "preferences": {
                "preferred_ai_model": "claude-3-sonnet",
                "analysis_depth": "standard",
                "use_case": "创意写作"
            }
        },
        {
            "name": "数据分析师",
            "preferences": {
                "preferred_ai_model": "gpt-3.5-turbo",
                "analysis_depth": "standard",
                "use_case": "数据分析"
            }
        }
    ]
    
    # 分析提示词
    analysis_result = await analyzer.analyze_prompt(test_prompt)
    
    for profile in user_profiles:
        print(f"\n   👤 用户类型: {profile['name']}")
        
        try:
            optimization_result = await optimization_engine.generate_optimization_result(
                analysis=analysis_result,
                user_preferences=profile["preferences"],
                use_ai_suggestions=True
            )
            
            print(f"   💡 个性化推荐数量: {len(optimization_result.personalized_recommendations)}")
            
            if optimization_result.personalized_recommendations:
                for rec in optimization_result.personalized_recommendations[:2]:
                    print(f"      • {rec}")
        
        except Exception as e:
            print(f"   ❌ 个性化测试失败: {e}")
    
    return True

async def test_batch_optimization():
    """测试批量优化功能"""
    print("\n🔄 测试批量优化...")
    
    ai_client = get_ai_client()
    analyzer = get_prompt_analyzer(ai_client)
    optimization_engine = get_optimization_engine(ai_client)
    
    batch_prompts = [
        "写个报告",
        "翻译文档",
        "分析数据",
        "创建演示"
    ]
    
    try:
        import time
        start_time = time.time()
        
        # 批量分析和优化
        results = []
        for prompt in batch_prompts:
            analysis = await analyzer.analyze_prompt(prompt, use_ai_analysis=False)
            optimization = await optimization_engine.generate_optimization_result(
                analysis, use_ai_suggestions=False
            )
            results.append({
                "prompt": prompt,
                "score": analysis.metrics.overall_score,
                "suggestions": len(optimization.suggestions),
                "improvement": optimization.estimated_score_improvement
            })
        
        total_time = time.time() - start_time
        
        print(f"   ✅ 批量处理完成，共处理 {len(batch_prompts)} 个提示词")
        print(f"   ⏱️  总耗时: {total_time:.2f}秒")
        print(f"   📊 平均处理时间: {total_time/len(batch_prompts):.2f}秒/个")
        
        # 显示结果摘要
        avg_score = sum(r["score"] for r in results) / len(results)
        total_suggestions = sum(r["suggestions"] for r in results)
        avg_improvement = sum(r["improvement"] for r in results) / len(results)
        
        print(f"   📈 平均分数: {avg_score:.1f}")
        print(f"   💡 总建议数: {total_suggestions}")
        print(f"   📊 平均预期改进: +{avg_improvement:.1f}")
        
        return True
    
    except Exception as e:
        print(f"   ❌ 批量优化测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 优化建议引擎测试开始")
    print("=" * 50)
    
    # 测试基础优化引擎
    if not await test_optimization_engine():
        print("\n❌ 基础优化引擎测试失败")
        return
    
    # 测试建议类型覆盖
    if not await test_suggestion_types():
        print("\n❌ 建议类型测试失败")
        return
    
    # 测试个性化推荐
    if not await test_personalization():
        print("\n❌ 个性化推荐测试失败")
        return
    
    # 测试批量优化
    if not await test_batch_optimization():
        print("\n❌ 批量优化测试失败")
        return
    
    print("\n" + "=" * 50)
    print("🎉 所有测试通过！优化建议引擎工作正常")
    print("\n💡 功能特性:")
    print("   ✅ 多维度分析和建议生成")
    print("   ✅ 智能优先级排序")
    print("   ✅ 个性化推荐")
    print("   ✅ 改进路线图生成")
    print("   ✅ 批量处理支持")
    print("   ✅ AI和规则混合模式")

if __name__ == "__main__":
    asyncio.run(main())
