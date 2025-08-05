"""
测试数据生成脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from config.database import SessionLocal, engine
from app.models import User, UserPreference, Prompt, Template, AnalysisResult, OptimizationSuggestion
import uuid
from datetime import datetime
import hashlib

def hash_password(password: str) -> str:
    """简单的密码哈希（生产环境应使用bcrypt）"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_test_users(db: Session):
    """创建测试用户"""
    users_data = [
        {
            "username": "admin",
            "email": "admin@enhanceprompt.com",
            "password": "admin123",
            "role": "admin"
        },
        {
            "username": "john_doe",
            "email": "john@example.com", 
            "password": "password123",
            "role": "user"
        },
        {
            "username": "jane_smith",
            "email": "jane@example.com",
            "password": "password123", 
            "role": "user"
        },
        {
            "username": "ai_engineer",
            "email": "engineer@example.com",
            "password": "password123",
            "role": "user"
        }
    ]
    
    created_users = []
    for user_data in users_data:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            print(f"用户 {user_data['email']} 已存在，跳过创建")
            created_users.append(existing_user)
            continue
            
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            password_hash=hash_password(user_data["password"]),
            role=user_data["role"],
            is_active=True
        )
        db.add(user)
        db.flush()  # 获取ID但不提交
        
        # 创建用户偏好
        preference = UserPreference(
            user_id=user.id,
            preferred_ai_model="gpt-3.5-turbo",
            analysis_depth="standard",
            notification_settings={"email": True, "push": False},
            ui_preferences={"theme": "light", "language": "zh-CN"}
        )
        db.add(preference)
        created_users.append(user)
        print(f"创建用户: {user.username} ({user.email})")
    
    return created_users

def create_test_templates(db: Session, users: list):
    """创建测试模板"""
    templates_data = [
        {
            "name": "创意写作助手",
            "description": "帮助用户进行创意写作的提示词模板",
            "content": "你是一个专业的创意写作助手。请根据用户提供的主题和要求，创作一篇富有想象力和创意的文章。要求：\n1. 语言生动有趣\n2. 情节引人入胜\n3. 字数控制在800-1200字\n4. 风格可以是{风格}",
            "category": "创作",
            "tags": ["写作", "创意", "文章"]
        },
        {
            "name": "代码审查助手",
            "description": "专业的代码审查和优化建议模板",
            "content": "你是一个资深的软件工程师。请仔细审查以下代码，并提供详细的反馈：\n\n代码：\n{代码内容}\n\n请从以下方面进行评估：\n1. 代码质量和可读性\n2. 性能优化建议\n3. 安全性问题\n4. 最佳实践建议\n5. 潜在的bug或问题",
            "category": "编程",
            "tags": ["代码审查", "编程", "优化"]
        },
        {
            "name": "数据分析报告",
            "description": "生成专业数据分析报告的模板",
            "content": "你是一个专业的数据分析师。请基于以下数据生成一份详细的分析报告：\n\n数据：{数据内容}\n\n报告应包含：\n1. 数据概览和关键指标\n2. 趋势分析\n3. 异常值识别\n4. 洞察和结论\n5. 行动建议",
            "category": "分析",
            "tags": ["数据分析", "报告", "洞察"]
        }
    ]
    
    created_templates = []
    for i, template_data in enumerate(templates_data):
        template = Template(
            creator_id=users[i % len(users)].id,
            name=template_data["name"],
            description=template_data["description"],
            content=template_data["content"],
            category=template_data["category"],
            tags=template_data["tags"],
            usage_count=0,
            rating=4.5,
            is_featured=i == 0,  # 第一个设为推荐
            is_public=True
        )
        db.add(template)
        created_templates.append(template)
        print(f"创建模板: {template.name}")
    
    return created_templates

def create_test_prompts(db: Session, users: list):
    """创建测试提示词"""
    prompts_data = [
        {
            "title": "产品介绍文案",
            "content": "请为我们的新产品写一份吸引人的介绍文案，产品是智能手表，主要功能包括健康监测、运动追踪、智能通知等。",
            "category": "营销",
            "tags": ["文案", "产品介绍", "营销"]
        },
        {
            "title": "Python函数优化",
            "content": "请帮我优化这个Python函数的性能：\n\ndef find_duplicates(lst):\n    duplicates = []\n    for i in range(len(lst)):\n        for j in range(i+1, len(lst)):\n            if lst[i] == lst[j] and lst[i] not in duplicates:\n                duplicates.append(lst[i])\n    return duplicates",
            "category": "编程",
            "tags": ["Python", "优化", "算法"]
        },
        {
            "title": "会议纪要总结",
            "content": "请帮我总结这次项目会议的要点，并整理成会议纪要格式。会议内容：讨论了新功能开发进度、遇到的技术难题、下周的工作安排等。",
            "category": "办公",
            "tags": ["会议", "总结", "纪要"]
        }
    ]
    
    created_prompts = []
    for i, prompt_data in enumerate(prompts_data):
        prompt = Prompt(
            user_id=users[i % len(users)].id,
            title=prompt_data["title"],
            content=prompt_data["content"],
            category=prompt_data["category"],
            tags=prompt_data["tags"],
            is_template=False,
            is_public=True
        )
        db.add(prompt)
        db.flush()
        
        # 为每个提示词创建分析结果
        analysis = AnalysisResult(
            prompt_id=prompt.id,
            overall_score=85 + (i * 5) % 15,  # 85-100之间的分数
            semantic_clarity=80 + (i * 3) % 20,
            structural_integrity=75 + (i * 4) % 25,
            logical_coherence=90 + (i * 2) % 10,
            analysis_details={
                "word_count": len(prompt.content.split()),
                "sentence_count": prompt.content.count('.') + prompt.content.count('!') + prompt.content.count('?'),
                "complexity_score": 7.5,
                "clarity_issues": [],
                "suggestions_count": 3
            },
            processing_time_ms=1500 + (i * 200),
            ai_model_used="gpt-3.5-turbo"
        )
        db.add(analysis)
        db.flush()
        
        # 为分析结果创建优化建议
        suggestions_data = [
            {
                "type": "clarity",
                "priority": 1,
                "description": "建议使用更具体的动词来增强表达的准确性",
                "plan": "将'做'、'进行'等通用动词替换为更精确的动词",
                "impact": "medium"
            },
            {
                "type": "structure", 
                "priority": 2,
                "description": "可以添加更多的上下文信息来提高指令的完整性",
                "plan": "在提示词开头添加角色设定和背景信息",
                "impact": "high"
            },
            {
                "type": "format",
                "priority": 3, 
                "description": "建议使用编号或分点的格式来提高可读性",
                "plan": "将长段落拆分为有序列表或要点",
                "impact": "low"
            }
        ]
        
        for j, sugg_data in enumerate(suggestions_data):
            suggestion = OptimizationSuggestion(
                analysis_id=analysis.id,
                suggestion_type=sugg_data["type"],
                priority=sugg_data["priority"],
                description=sugg_data["description"],
                improvement_plan=sugg_data["plan"],
                expected_impact=sugg_data["impact"],
                is_applied=j == 0  # 第一个建议标记为已应用
            )
            db.add(suggestion)
        
        created_prompts.append(prompt)
        print(f"创建提示词: {prompt.title}")
    
    return created_prompts

def main():
    """主函数"""
    print("🌱 开始生成测试数据...")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 创建测试用户
        print("\n👥 创建测试用户...")
        users = create_test_users(db)
        
        # 创建测试模板
        print("\n📋 创建测试模板...")
        templates = create_test_templates(db, users)
        
        # 创建测试提示词
        print("\n💬 创建测试提示词...")
        prompts = create_test_prompts(db, users)
        
        # 提交所有更改
        db.commit()
        print("\n✅ 测试数据生成完成！")
        print(f"   - 用户: {len(users)} 个")
        print(f"   - 模板: {len(templates)} 个") 
        print(f"   - 提示词: {len(prompts)} 个")
        
    except Exception as e:
        print(f"\n❌ 生成测试数据时出错: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
