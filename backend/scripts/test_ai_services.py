"""
AI服务测试脚本
"""

import sys
import os
import asyncio
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.ai_client import get_ai_client, AIClientError
from app.services.prompt_analyzer import get_prompt_analyzer

async def test_ai_client():
    """测试AI客户端基础功能"""
    print("🤖 测试AI客户端...")
    
    ai_client = get_ai_client()
    
    # 检查可用模型
    available_models = ai_client.get_available_models()
    print(f"📋 可用模型: {available_models}")
    
    if not available_models:
        print("❌ 没有可用的AI模型，请检查API密钥配置")
        return False
    
    # 测试每个可用模型
    test_prompt = "请简单回复'测试成功'来确认连接正常。"
    
    for model in available_models[:2]:  # 只测试前两个模型以节省成本
        print(f"\n🔍 测试模型: {model}")
        
        try:
            start_time = time.time()
            response = await ai_client.generate_completion(
                prompt=test_prompt,
                model=model,
                temperature=0.1,
                max_tokens=50
            )
            
            print(f"✅ 响应: {response.content}")
            print(f"⏱️  响应时间: {response.response_time:.2f}秒")
            print(f"🔢 Token使用: {response.usage}")
            
        except AIClientError as e:
            print(f"❌ 模型 {model} 测试失败: {e}")
            return False
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            return False
    
    return True

async def test_prompt_analyzer():
    """测试提示词分析器"""
    print("\n📊 测试提示词分析器...")
    
    ai_client = get_ai_client()
    analyzer = get_prompt_analyzer(ai_client)
    
    # 测试提示词
    test_prompts = [
        "写一篇文章",  # 简单模糊的提示词
        "请你作为一个专业的技术写作专家，为我写一篇关于人工智能在医疗领域应用的技术文章。文章应该包含以下要点：1. AI在诊断中的应用 2. 机器学习在药物发现中的作用 3. 未来发展趋势。文章长度控制在1500字左右，语言要专业但易懂。",  # 详细具体的提示词
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 测试提示词 {i}: {prompt[:50]}...")
        
        try:
            # 执行分析
            result = await analyzer.analyze_prompt(
                text=prompt,
                model=ai_client.get_available_models()[0] if ai_client.get_available_models() else "rule-based",
                use_ai_analysis=len(ai_client.get_available_models()) > 0
            )
            
            print(f"📊 总体评分: {result.metrics.overall_score}/100")
            print(f"🎯 语义清晰度: {result.metrics.semantic_clarity}/100")
            print(f"🏗️  结构完整性: {result.metrics.structural_integrity}/100")
            print(f"🔗 逻辑连贯性: {result.metrics.logical_coherence}/100")
            print(f"🎯 具体性程度: {result.metrics.specificity_score}/100")
            print(f"📋 指令清晰度: {result.metrics.instruction_clarity}/100")
            print(f"⏱️  处理时间: {result.processing_time:.2f}秒")
            print(f"🤖 使用模型: {result.model_used}")
            
            if result.strengths:
                print(f"✅ 优点: {', '.join(result.strengths[:3])}")
            
            if result.weaknesses:
                print(f"⚠️  缺点: {', '.join(result.weaknesses[:3])}")
            
            if result.suggestions:
                print(f"💡 建议: {', '.join(result.suggestions[:3])}")
        
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            return False
    
    return True

async def test_batch_analysis():
    """测试批量分析功能"""
    print("\n🔄 测试批量分析...")
    
    ai_client = get_ai_client()
    
    if not ai_client.get_available_models():
        print("⚠️  跳过批量分析测试（无可用AI模型）")
        return True
    
    test_prompts = [
        "翻译这段文字",
        "总结这篇文章的要点",
        "分析这个数据的趋势"
    ]
    
    try:
        start_time = time.time()
        responses = await ai_client.batch_generate(
            prompts=test_prompts,
            model=ai_client.get_available_models()[0],
            system_prompt="请简短回复，确认收到指令。",
            max_concurrent=2
        )
        
        total_time = time.time() - start_time
        print(f"✅ 批量分析完成，共处理 {len(responses)} 个提示词")
        print(f"⏱️  总耗时: {total_time:.2f}秒")
        print(f"📊 平均响应时间: {total_time/len(responses):.2f}秒")
        
        return True
    
    except Exception as e:
        print(f"❌ 批量分析失败: {e}")
        return False

async def test_cost_calculation():
    """测试成本计算功能"""
    print("\n💰 测试成本计算...")
    
    ai_client = get_ai_client()
    
    test_text = "这是一个用于测试token计算和成本估算的示例文本。" * 10
    
    for model in ["gpt-3.5-turbo", "gpt-4", "claude-3-haiku", "claude-3-sonnet"]:
        token_count = ai_client.count_tokens(test_text, model)
        print(f"📝 模型 {model}: {token_count} tokens")
    
    return True

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    print(f"🔑 OpenAI API Key: {'✅ 已配置' if openai_key else '❌ 未配置'}")
    print(f"🔑 Anthropic API Key: {'✅ 已配置' if anthropic_key else '❌ 未配置'}")
    
    if not openai_key and not anthropic_key:
        print("⚠️  警告: 没有配置任何AI服务API密钥")
        print("💡 请在.env文件中配置OPENAI_API_KEY或ANTHROPIC_API_KEY")
        return False
    
    return True

async def main():
    """主测试函数"""
    print("🧪 AI服务测试开始")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请配置API密钥后重试")
        return
    
    # 测试AI客户端
    if not await test_ai_client():
        print("\n❌ AI客户端测试失败")
        return
    
    # 测试提示词分析器
    if not await test_prompt_analyzer():
        print("\n❌ 提示词分析器测试失败")
        return
    
    # 测试批量分析
    if not await test_batch_analysis():
        print("\n❌ 批量分析测试失败")
        return
    
    # 测试成本计算
    if not await test_cost_calculation():
        print("\n❌ 成本计算测试失败")
        return
    
    print("\n" + "=" * 50)
    print("🎉 所有测试通过！AI服务集成成功")
    print("\n💡 使用建议:")
    print("   - 在生产环境中设置合适的API限流")
    print("   - 监控API使用成本")
    print("   - 定期检查模型可用性")

if __name__ == "__main__":
    asyncio.run(main())
