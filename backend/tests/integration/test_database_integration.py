"""
数据库集成测试
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.prompt import Prompt
from app.models.template import Template
from app.models.analysis import Analysis


@pytest.mark.integration
class TestDatabaseTransactions:
    """数据库事务测试"""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, integration_db_session: AsyncSession):
        """测试事务回滚"""
        # 开始事务
        async with integration_db_session.begin():
            # 创建用户
            user = User(
                username="transaction_test_user",
                email="transaction@test.com",
                hashed_password="hashed_password"
            )
            integration_db_session.add(user)
            await integration_db_session.flush()  # 获取ID但不提交
            
            user_id = user.id
            assert user_id is not None
            
            # 模拟错误，触发回滚
            raise Exception("模拟错误")
        
        # 验证事务已回滚，用户不存在
        result = await integration_db_session.execute(
            text("SELECT * FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        assert result.fetchone() is None
    
    @pytest.mark.asyncio
    async def test_transaction_commit(self, integration_db_session: AsyncSession):
        """测试事务提交"""
        # 创建用户
        user = User(
            username="commit_test_user",
            email="commit@test.com",
            hashed_password="hashed_password"
        )
        integration_db_session.add(user)
        await integration_db_session.commit()
        
        user_id = user.id
        
        # 验证用户已保存
        result = await integration_db_session.execute(
            text("SELECT * FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        saved_user = result.fetchone()
        assert saved_user is not None
        assert saved_user.username == "commit_test_user"
    
    @pytest.mark.asyncio
    async def test_nested_transactions(self, integration_db_session: AsyncSession):
        """测试嵌套事务"""
        # 外层事务
        async with integration_db_session.begin():
            user = User(
                username="nested_test_user",
                email="nested@test.com",
                hashed_password="hashed_password"
            )
            integration_db_session.add(user)
            await integration_db_session.flush()
            
            # 内层事务（保存点）
            async with integration_db_session.begin_nested():
                prompt = Prompt(
                    title="嵌套事务测试",
                    content="测试内容",
                    user_id=user.id
                )
                integration_db_session.add(prompt)
                await integration_db_session.flush()
                
                # 内层回滚
                await integration_db_session.rollback()
            
            # 外层提交
            await integration_db_session.commit()
        
        # 验证用户存在，但提示词不存在
        user_result = await integration_db_session.execute(
            text("SELECT * FROM users WHERE username = 'nested_test_user'")
        )
        assert user_result.fetchone() is not None
        
        prompt_result = await integration_db_session.execute(
            text("SELECT * FROM prompts WHERE title = '嵌套事务测试'")
        )
        assert prompt_result.fetchone() is None


@pytest.mark.integration
class TestDatabaseConstraints:
    """数据库约束测试"""
    
    @pytest.mark.asyncio
    async def test_unique_constraints(self, integration_db_session: AsyncSession):
        """测试唯一约束"""
        # 创建第一个用户
        user1 = User(
            username="unique_test",
            email="unique@test.com",
            hashed_password="password1"
        )
        integration_db_session.add(user1)
        await integration_db_session.commit()
        
        # 尝试创建相同用户名的用户
        user2 = User(
            username="unique_test",  # 相同用户名
            email="unique2@test.com",
            hashed_password="password2"
        )
        integration_db_session.add(user2)
        
        with pytest.raises(Exception):  # 应该抛出唯一约束异常
            await integration_db_session.commit()
        
        await integration_db_session.rollback()
        
        # 尝试创建相同邮箱的用户
        user3 = User(
            username="unique_test2",
            email="unique@test.com",  # 相同邮箱
            hashed_password="password3"
        )
        integration_db_session.add(user3)
        
        with pytest.raises(Exception):  # 应该抛出唯一约束异常
            await integration_db_session.commit()
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, integration_db_session: AsyncSession):
        """测试外键约束"""
        # 尝试创建引用不存在用户的提示词
        prompt = Prompt(
            title="外键测试",
            content="测试内容",
            user_id=99999  # 不存在的用户ID
        )
        integration_db_session.add(prompt)
        
        with pytest.raises(Exception):  # 应该抛出外键约束异常
            await integration_db_session.commit()
    
    @pytest.mark.asyncio
    async def test_not_null_constraints(self, integration_db_session: AsyncSession):
        """测试非空约束"""
        # 尝试创建缺少必填字段的用户
        user = User(
            username=None,  # 必填字段为空
            email="notnull@test.com",
            hashed_password="password"
        )
        integration_db_session.add(user)
        
        with pytest.raises(Exception):  # 应该抛出非空约束异常
            await integration_db_session.commit()


@pytest.mark.integration
class TestDatabaseRelationships:
    """数据库关系测试"""
    
    @pytest.mark.asyncio
    async def test_one_to_many_relationship(self, integration_db_session: AsyncSession):
        """测试一对多关系"""
        # 创建用户
        user = User(
            username="relationship_test",
            email="relationship@test.com",
            hashed_password="password"
        )
        integration_db_session.add(user)
        await integration_db_session.commit()
        
        # 创建多个提示词
        prompts = []
        for i in range(3):
            prompt = Prompt(
                title=f"提示词{i}",
                content=f"内容{i}",
                user_id=user.id
            )
            prompts.append(prompt)
            integration_db_session.add(prompt)
        
        await integration_db_session.commit()
        
        # 验证关系
        await integration_db_session.refresh(user)
        assert len(user.prompts) == 3
        
        for i, prompt in enumerate(user.prompts):
            assert prompt.title == f"提示词{i}"
            assert prompt.user_id == user.id
    
    @pytest.mark.asyncio
    async def test_cascade_delete(self, integration_db_session: AsyncSession):
        """测试级联删除"""
        # 创建用户和相关数据
        user = User(
            username="cascade_test",
            email="cascade@test.com",
            hashed_password="password"
        )
        integration_db_session.add(user)
        await integration_db_session.commit()
        
        # 创建提示词
        prompt = Prompt(
            title="级联测试提示词",
            content="测试内容",
            user_id=user.id
        )
        integration_db_session.add(prompt)
        await integration_db_session.commit()
        
        # 创建分析
        analysis = Analysis(
            prompt_id=prompt.id,
            user_id=user.id,
            overall_score=85.0,
            semantic_clarity=90.0,
            structural_integrity=80.0,
            logical_coherence=85.0,
            analysis_details={"test": True},
            suggestions=["测试建议"],
            ai_model_used="test-model",
            processing_time_ms=1000
        )
        integration_db_session.add(analysis)
        await integration_db_session.commit()
        
        prompt_id = prompt.id
        analysis_id = analysis.id
        
        # 删除用户
        await integration_db_session.delete(user)
        await integration_db_session.commit()
        
        # 验证相关数据是否被级联删除（取决于配置）
        prompt_result = await integration_db_session.execute(
            text("SELECT * FROM prompts WHERE id = :prompt_id"),
            {"prompt_id": prompt_id}
        )
        
        analysis_result = await integration_db_session.execute(
            text("SELECT * FROM analyses WHERE id = :analysis_id"),
            {"analysis_id": analysis_id}
        )
        
        # 根据实际的级联配置验证结果
        # 这里假设配置了级联删除
        assert prompt_result.fetchone() is None
        assert analysis_result.fetchone() is None


@pytest.mark.integration
class TestDatabasePerformance:
    """数据库性能测试"""
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, integration_db_session: AsyncSession):
        """测试批量插入性能"""
        import time
        
        # 创建用户
        user = User(
            username="bulk_test",
            email="bulk@test.com",
            hashed_password="password"
        )
        integration_db_session.add(user)
        await integration_db_session.commit()
        
        # 批量创建数据
        start_time = time.time()
        
        templates = []
        for i in range(100):
            template = Template(
                name=f"批量模板{i}",
                content=f"批量内容{i}",
                user_id=user.id
            )
            templates.append(template)
        
        integration_db_session.add_all(templates)
        await integration_db_session.commit()
        
        end_time = time.time()
        insert_time = end_time - start_time
        
        # 验证插入时间合理（应该在几秒内完成）
        assert insert_time < 10.0  # 10秒内完成
        
        # 验证数据正确插入
        result = await integration_db_session.execute(
            text("SELECT COUNT(*) FROM templates WHERE user_id = :user_id"),
            {"user_id": user.id}
        )
        count = result.scalar()
        assert count == 100
    
    @pytest.mark.asyncio
    async def test_query_performance_with_indexes(self, integration_db_session: AsyncSession):
        """测试带索引的查询性能"""
        import time
        
        # 创建用户
        user = User(
            username="query_test",
            email="query@test.com",
            hashed_password="password"
        )
        integration_db_session.add(user)
        await integration_db_session.commit()
        
        # 创建大量数据
        prompts = []
        for i in range(1000):
            prompt = Prompt(
                title=f"查询测试{i}",
                content=f"内容{i}",
                category=f"分类{i % 10}",
                user_id=user.id
            )
            prompts.append(prompt)
        
        integration_db_session.add_all(prompts)
        await integration_db_session.commit()
        
        # 测试查询性能
        start_time = time.time()
        
        # 按分类查询（应该有索引）
        result = await integration_db_session.execute(
            text("SELECT * FROM prompts WHERE category = :category"),
            {"category": "分类5"}
        )
        results = result.fetchall()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # 验证查询时间合理
        assert query_time < 1.0  # 1秒内完成
        assert len(results) == 100  # 应该找到100条记录


@pytest.mark.integration
class TestDatabaseConsistency:
    """数据库一致性测试"""
    
    @pytest.mark.asyncio
    async def test_data_consistency_across_operations(self, integration_db_session: AsyncSession):
        """测试跨操作的数据一致性"""
        # 创建用户
        user = User(
            username="consistency_test",
            email="consistency@test.com",
            hashed_password="password"
        )
        integration_db_session.add(user)
        await integration_db_session.commit()
        
        # 创建提示词
        prompt = Prompt(
            title="一致性测试",
            content="测试内容",
            user_id=user.id
        )
        integration_db_session.add(prompt)
        await integration_db_session.commit()
        
        # 创建分析
        analysis = Analysis(
            prompt_id=prompt.id,
            user_id=user.id,
            overall_score=85.0,
            semantic_clarity=90.0,
            structural_integrity=80.0,
            logical_coherence=85.0,
            analysis_details={"consistency": "test"},
            suggestions=["一致性测试建议"],
            ai_model_used="test-model",
            processing_time_ms=1000
        )
        integration_db_session.add(analysis)
        await integration_db_session.commit()
        
        # 验证数据一致性
        # 1. 分析应该正确关联到提示词和用户
        await integration_db_session.refresh(analysis)
        assert analysis.prompt_id == prompt.id
        assert analysis.user_id == user.id
        
        # 2. 提示词应该有相关的分析
        await integration_db_session.refresh(prompt)
        assert len(prompt.analyses) == 1
        assert prompt.analyses[0].id == analysis.id
        
        # 3. 用户应该有相关的提示词和分析
        await integration_db_session.refresh(user)
        assert len(user.prompts) == 1
        assert len(user.analyses) == 1
        assert user.prompts[0].id == prompt.id
        assert user.analyses[0].id == analysis.id
    
    @pytest.mark.asyncio
    async def test_concurrent_access_consistency(self, integration_db_session: AsyncSession):
        """测试并发访问一致性"""
        import asyncio
        
        # 创建用户
        user = User(
            username="concurrent_test",
            email="concurrent@test.com",
            hashed_password="password"
        )
        integration_db_session.add(user)
        await integration_db_session.commit()
        
        # 模拟并发创建提示词
        async def create_prompt(index):
            prompt = Prompt(
                title=f"并发提示词{index}",
                content=f"并发内容{index}",
                user_id=user.id
            )
            integration_db_session.add(prompt)
            await integration_db_session.commit()
            return prompt.id
        
        # 并发执行
        tasks = [create_prompt(i) for i in range(5)]
        prompt_ids = await asyncio.gather(*tasks)
        
        # 验证所有提示词都被正确创建
        assert len(prompt_ids) == 5
        assert len(set(prompt_ids)) == 5  # 所有ID都不同
        
        # 验证用户关联正确
        await integration_db_session.refresh(user)
        assert len(user.prompts) == 5
