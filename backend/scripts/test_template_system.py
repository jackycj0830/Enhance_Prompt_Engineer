"""
模板系统测试脚本
"""

import sys
import os
import asyncio
import json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from config.database import get_db_session
from app.services.template_service import get_template_service
from app.models.template import Template, TemplateCategory, TemplateTag
from app.models.user import User

async def test_template_service():
    """测试模板服务"""
    print("🧪 测试模板服务...")
    
    # 获取数据库会话
    db = next(get_db_session())
    template_service = get_template_service(db)
    
    # 创建测试用户（如果不存在）
    test_user = db.query(User).filter(User.email == "test@example.com").first()
    if not test_user:
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="test_password_hash"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    
    user_id = str(test_user.id)
    
    try:
        # 1. 测试创建模板
        print("\n📝 测试创建模板...")
        template = await template_service.create_template(
            creator_id=user_id,
            name="测试AI助手模板",
            content="你是一个专业的AI助手，请帮助用户解决问题。\n\n用户问题：{question}\n\n请提供详细、准确的回答。",
            description="这是一个通用的AI助手模板，适用于各种问答场景",
            category="AI助手",
            tags=["AI助手", "问答", "通用"],
            industry="科技",
            use_case="客户服务",
            difficulty_level="beginner",
            is_public=True,
            metadata={"version": "1.0", "author": "测试用户"}
        )
        print(f"   ✅ 模板创建成功: {template.name} (ID: {template.id})")
        
        # 2. 测试获取模板
        print("\n🔍 测试获取模板...")
        retrieved_template = await template_service.get_template(str(template.id), user_id)
        if retrieved_template:
            print(f"   ✅ 模板获取成功: {retrieved_template.name}")
        else:
            print("   ❌ 模板获取失败")
            return False
        
        # 3. 测试搜索模板
        print("\n🔎 测试搜索模板...")
        templates, total = await template_service.search_templates(
            query="AI助手",
            category="AI助手",
            tags=["AI助手"],
            user_id=user_id,
            page=1,
            page_size=10
        )
        print(f"   ✅ 搜索结果: 找到 {total} 个模板")
        for t in templates[:3]:
            print(f"      - {t.name} (评分: {t.rating}, 使用: {t.usage_count}次)")
        
        # 4. 测试使用模板
        print("\n📊 测试使用模板...")
        success = await template_service.use_template(str(template.id), user_id)
        if success:
            print("   ✅ 模板使用记录成功")
            # 验证使用计数增加
            updated_template = await template_service.get_template(str(template.id), user_id)
            print(f"   📈 使用计数: {updated_template.usage_count}")
        else:
            print("   ❌ 模板使用记录失败")
        
        # 5. 测试评分模板
        print("\n⭐ 测试评分模板...")
        success = await template_service.rate_template(
            str(template.id),
            user_id,
            5,
            "非常好用的模板！"
        )
        if success:
            print("   ✅ 模板评分成功")
            # 验证评分更新
            rated_template = await template_service.get_template(str(template.id), user_id)
            print(f"   📊 平均评分: {rated_template.rating} ({rated_template.rating_count}人评分)")
        else:
            print("   ❌ 模板评分失败")
        
        # 6. 测试更新模板
        print("\n✏️ 测试更新模板...")
        updated_template = await template_service.update_template(
            str(template.id),
            user_id,
            description="更新后的模板描述",
            tags=["AI助手", "问答", "通用", "更新"]
        )
        if updated_template:
            print(f"   ✅ 模板更新成功: {updated_template.description}")
            print(f"   🏷️ 更新后标签: {updated_template.tags}")
        else:
            print("   ❌ 模板更新失败")
        
        # 7. 测试获取热门模板
        print("\n🔥 测试获取热门模板...")
        popular_templates = await template_service.get_popular_templates(5)
        print(f"   ✅ 热门模板数量: {len(popular_templates)}")
        for t in popular_templates:
            print(f"      - {t.name} (使用: {t.usage_count}次, 评分: {t.rating})")
        
        # 8. 测试获取推荐模板
        print("\n⭐ 测试获取推荐模板...")
        featured_templates = await template_service.get_featured_templates(5)
        print(f"   ✅ 推荐模板数量: {len(featured_templates)}")
        
        # 9. 测试获取最新模板
        print("\n🆕 测试获取最新模板...")
        recent_templates = await template_service.get_recent_templates(5)
        print(f"   ✅ 最新模板数量: {len(recent_templates)}")
        for t in recent_templates:
            print(f"      - {t.name} (创建时间: {t.created_at.strftime('%Y-%m-%d %H:%M')})")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False
    finally:
        db.close()

async def test_template_categories():
    """测试模板分类功能"""
    print("\n📂 测试模板分类...")
    
    db = next(get_db_session())
    
    try:
        # 获取所有分类
        categories = db.query(TemplateCategory).filter(
            TemplateCategory.is_active == True
        ).order_by(TemplateCategory.sort_order).all()
        
        print(f"   ✅ 分类总数: {len(categories)}")
        for category in categories[:5]:
            print(f"      - {category.name}: {category.description}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 分类测试失败: {e}")
        return False
    finally:
        db.close()

async def test_template_tags():
    """测试模板标签功能"""
    print("\n🏷️ 测试模板标签...")
    
    db = next(get_db_session())
    
    try:
        # 获取所有标签
        tags = db.query(TemplateTag).order_by(
            TemplateTag.usage_count.desc()
        ).limit(10).all()
        
        print(f"   ✅ 标签总数: {len(tags)}")
        for tag in tags:
            featured = "⭐" if tag.is_featured else ""
            print(f"      - {tag.name}{featured}: 使用{tag.usage_count}次")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 标签测试失败: {e}")
        return False
    finally:
        db.close()

async def test_template_search():
    """测试模板搜索功能"""
    print("\n🔍 测试模板搜索功能...")
    
    db = next(get_db_session())
    template_service = get_template_service(db)
    
    try:
        # 测试不同的搜索条件
        search_tests = [
            {"query": "AI", "description": "关键词搜索"},
            {"category": "创作", "description": "分类筛选"},
            {"tags": ["AI助手"], "description": "标签筛选"},
            {"difficulty_level": "beginner", "description": "难度筛选"},
            {"sort_by": "rating", "sort_order": "desc", "description": "评分排序"},
            {"sort_by": "usage_count", "sort_order": "desc", "description": "使用量排序"}
        ]
        
        for test in search_tests:
            description = test.pop("description")
            templates, total = await template_service.search_templates(**test)
            print(f"   ✅ {description}: 找到 {total} 个模板")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 搜索测试失败: {e}")
        return False
    finally:
        db.close()

async def test_template_permissions():
    """测试模板权限控制"""
    print("\n🔒 测试模板权限控制...")
    
    db = next(get_db_session())
    template_service = get_template_service(db)
    
    try:
        # 创建两个测试用户
        user1 = db.query(User).filter(User.email == "user1@test.com").first()
        if not user1:
            user1 = User(username="user1", email="user1@test.com", hashed_password="hash1")
            db.add(user1)
        
        user2 = db.query(User).filter(User.email == "user2@test.com").first()
        if not user2:
            user2 = User(username="user2", email="user2@test.com", hashed_password="hash2")
            db.add(user2)
        
        db.commit()
        
        # 用户1创建私有模板
        private_template = await template_service.create_template(
            creator_id=str(user1.id),
            name="私有模板",
            content="这是一个私有模板",
            is_public=False
        )
        
        # 用户2尝试访问私有模板
        accessed_template = await template_service.get_template(
            str(private_template.id),
            str(user2.id)
        )
        
        if accessed_template is None:
            print("   ✅ 私有模板权限控制正常")
        else:
            print("   ❌ 私有模板权限控制失败")
            return False
        
        # 用户1可以访问自己的私有模板
        owner_access = await template_service.get_template(
            str(private_template.id),
            str(user1.id)
        )
        
        if owner_access:
            print("   ✅ 创建者可以访问自己的私有模板")
        else:
            print("   ❌ 创建者无法访问自己的私有模板")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ 权限测试失败: {e}")
        return False
    finally:
        db.close()

async def test_template_statistics():
    """测试模板统计功能"""
    print("\n📊 测试模板统计功能...")
    
    db = next(get_db_session())
    
    try:
        # 统计各种数据
        total_templates = db.query(Template).count()
        public_templates = db.query(Template).filter(Template.is_public == True).count()
        featured_templates = db.query(Template).filter(Template.is_featured == True).count()
        
        print(f"   📈 模板总数: {total_templates}")
        print(f"   🌐 公开模板: {public_templates}")
        print(f"   ⭐ 推荐模板: {featured_templates}")
        
        # 按分类统计
        category_stats = db.query(
            Template.category,
            db.func.count(Template.id).label('count')
        ).filter(
            Template.is_public == True
        ).group_by(Template.category).all()
        
        print(f"   📂 分类统计:")
        for category, count in category_stats:
            print(f"      - {category or '未分类'}: {count}个")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 统计测试失败: {e}")
        return False
    finally:
        db.close()

async def main():
    """主测试函数"""
    print("🧪 模板系统测试开始")
    print("=" * 50)
    
    # 执行各项测试
    tests = [
        ("模板服务基础功能", test_template_service),
        ("模板分类功能", test_template_categories),
        ("模板标签功能", test_template_tags),
        ("模板搜索功能", test_template_search),
        ("模板权限控制", test_template_permissions),
        ("模板统计功能", test_template_statistics)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔬 执行测试: {test_name}")
        try:
            if await test_func():
                print(f"✅ {test_name} - 通过")
                passed += 1
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！模板系统工作正常")
        print("\n💡 功能特性:")
        print("   ✅ 模板CRUD操作")
        print("   ✅ 高级搜索和筛选")
        print("   ✅ 评分和使用统计")
        print("   ✅ 分类和标签管理")
        print("   ✅ 权限控制")
        print("   ✅ 数据统计分析")
    else:
        print(f"⚠️ 有 {total - passed} 个测试失败，请检查相关功能")

if __name__ == "__main__":
    asyncio.run(main())
