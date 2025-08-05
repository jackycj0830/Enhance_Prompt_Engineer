"""Add performance indexes

Revision ID: add_performance_indexes
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """添加性能优化索引"""
    
    # 用户表索引
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    
    # 提示词表索引
    op.create_index('idx_prompts_user_id', 'prompts', ['user_id'])
    op.create_index('idx_prompts_category', 'prompts', ['category'])
    op.create_index('idx_prompts_is_public', 'prompts', ['is_public'])
    op.create_index('idx_prompts_created_at', 'prompts', ['created_at'])
    op.create_index('idx_prompts_updated_at', 'prompts', ['updated_at'])
    op.create_index('idx_prompts_user_created', 'prompts', ['user_id', 'created_at'])
    op.create_index('idx_prompts_public_category', 'prompts', ['is_public', 'category'])
    
    # 模板表索引
    op.create_index('idx_templates_user_id', 'templates', ['user_id'])
    op.create_index('idx_templates_category', 'templates', ['category'])
    op.create_index('idx_templates_is_public', 'templates', ['is_public'])
    op.create_index('idx_templates_is_featured', 'templates', ['is_featured'])
    op.create_index('idx_templates_created_at', 'templates', ['created_at'])
    op.create_index('idx_templates_usage_count', 'templates', ['usage_count'])
    op.create_index('idx_templates_user_created', 'templates', ['user_id', 'created_at'])
    op.create_index('idx_templates_public_featured', 'templates', ['is_public', 'is_featured'])
    op.create_index('idx_templates_category_usage', 'templates', ['category', 'usage_count'])
    
    # 分析表索引
    op.create_index('idx_analyses_user_id', 'analyses', ['user_id'])
    op.create_index('idx_analyses_prompt_id', 'analyses', ['prompt_id'])
    op.create_index('idx_analyses_created_at', 'analyses', ['created_at'])
    op.create_index('idx_analyses_overall_score', 'analyses', ['overall_score'])
    op.create_index('idx_analyses_ai_model', 'analyses', ['ai_model_used'])
    op.create_index('idx_analyses_user_created', 'analyses', ['user_id', 'created_at'])
    op.create_index('idx_analyses_prompt_created', 'analyses', ['prompt_id', 'created_at'])
    op.create_index('idx_analyses_score_created', 'analyses', ['overall_score', 'created_at'])
    
    # 全文搜索索引（如果支持）
    try:
        # PostgreSQL全文搜索索引
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_prompts_title_fts 
            ON prompts USING gin(to_tsvector('english', title))
        """)
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_prompts_content_fts 
            ON prompts USING gin(to_tsvector('english', content))
        """)
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_templates_name_fts 
            ON templates USING gin(to_tsvector('english', name))
        """)
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_templates_content_fts 
            ON templates USING gin(to_tsvector('english', content))
        """)
    except Exception:
        # SQLite或其他数据库的降级处理
        pass
    
    # 复合索引用于常见查询模式
    op.create_index('idx_prompts_user_public_category', 'prompts', 
                   ['user_id', 'is_public', 'category'])
    op.create_index('idx_templates_user_public_category', 'templates', 
                   ['user_id', 'is_public', 'category'])
    op.create_index('idx_analyses_user_prompt_created', 'analyses', 
                   ['user_id', 'prompt_id', 'created_at'])


def downgrade():
    """删除性能优化索引"""
    
    # 删除用户表索引
    op.drop_index('idx_users_username')
    op.drop_index('idx_users_email')
    op.drop_index('idx_users_is_active')
    op.drop_index('idx_users_created_at')
    
    # 删除提示词表索引
    op.drop_index('idx_prompts_user_id')
    op.drop_index('idx_prompts_category')
    op.drop_index('idx_prompts_is_public')
    op.drop_index('idx_prompts_created_at')
    op.drop_index('idx_prompts_updated_at')
    op.drop_index('idx_prompts_user_created')
    op.drop_index('idx_prompts_public_category')
    
    # 删除模板表索引
    op.drop_index('idx_templates_user_id')
    op.drop_index('idx_templates_category')
    op.drop_index('idx_templates_is_public')
    op.drop_index('idx_templates_is_featured')
    op.drop_index('idx_templates_created_at')
    op.drop_index('idx_templates_usage_count')
    op.drop_index('idx_templates_user_created')
    op.drop_index('idx_templates_public_featured')
    op.drop_index('idx_templates_category_usage')
    
    # 删除分析表索引
    op.drop_index('idx_analyses_user_id')
    op.drop_index('idx_analyses_prompt_id')
    op.drop_index('idx_analyses_created_at')
    op.drop_index('idx_analyses_overall_score')
    op.drop_index('idx_analyses_ai_model')
    op.drop_index('idx_analyses_user_created')
    op.drop_index('idx_analyses_prompt_created')
    op.drop_index('idx_analyses_score_created')
    
    # 删除全文搜索索引
    try:
        op.execute("DROP INDEX IF EXISTS idx_prompts_title_fts")
        op.execute("DROP INDEX IF EXISTS idx_prompts_content_fts")
        op.execute("DROP INDEX IF EXISTS idx_templates_name_fts")
        op.execute("DROP INDEX IF EXISTS idx_templates_content_fts")
    except Exception:
        pass
    
    # 删除复合索引
    op.drop_index('idx_prompts_user_public_category')
    op.drop_index('idx_templates_user_public_category')
    op.drop_index('idx_analyses_user_prompt_created')
