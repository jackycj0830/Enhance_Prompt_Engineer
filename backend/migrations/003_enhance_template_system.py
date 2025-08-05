"""
增强模板系统数据库迁移
添加新的模板相关表和字段
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    """升级数据库结构"""
    
    # 1. 为templates表添加新字段
    op.add_column('templates', sa.Column('rating_count', sa.Integer(), default=0))
    op.add_column('templates', sa.Column('is_verified', sa.Boolean(), default=False))
    op.add_column('templates', sa.Column('difficulty_level', sa.String(20), default='beginner'))
    op.add_column('templates', sa.Column('language', sa.String(10), default='zh-CN'))
    op.add_column('templates', sa.Column('industry', sa.String(50), nullable=True))
    op.add_column('templates', sa.Column('use_case', sa.String(100), nullable=True))
    op.add_column('templates', sa.Column('metadata', postgresql.JSONB(), default={}))
    op.add_column('templates', sa.Column('version', sa.String(20), default='1.0.0'))
    op.add_column('templates', sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_templates_parent_id',
        'templates', 'templates',
        ['parent_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # 2. 创建template_collections表
    op.create_table(
        'template_collections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collection_name', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ondelete='CASCADE')
    )
    
    # 3. 创建template_categories表
    op.create_table(
        'template_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['parent_id'], ['template_categories.id'], ondelete='CASCADE')
    )
    
    # 4. 创建template_tags表
    op.create_table(
        'template_tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('is_featured', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # 5. 创建索引
    # templates表索引
    op.create_index('idx_template_category', 'templates', ['category'])
    op.create_index('idx_template_tags', 'templates', ['tags'])
    op.create_index('idx_template_industry', 'templates', ['industry'])
    op.create_index('idx_template_difficulty', 'templates', ['difficulty_level'])
    op.create_index('idx_template_public', 'templates', ['is_public'])
    op.create_index('idx_template_featured', 'templates', ['is_featured'])
    op.create_index('idx_template_rating', 'templates', ['rating'])
    op.create_index('idx_template_usage', 'templates', ['usage_count'])
    op.create_index('idx_template_verified', 'templates', ['is_verified'])
    op.create_index('idx_template_language', 'templates', ['language'])
    
    # template_collections表索引
    op.create_index('idx_collection_user', 'template_collections', ['user_id'])
    op.create_index('idx_collection_template', 'template_collections', ['template_id'])
    op.create_index('idx_collection_name', 'template_collections', ['collection_name'])
    
    # template_categories表索引
    op.create_index('idx_category_name', 'template_categories', ['name'])
    op.create_index('idx_category_parent', 'template_categories', ['parent_id'])
    op.create_index('idx_category_active', 'template_categories', ['is_active'])
    op.create_index('idx_category_sort', 'template_categories', ['sort_order'])
    
    # template_tags表索引
    op.create_index('idx_tag_name', 'template_tags', ['name'])
    op.create_index('idx_tag_usage', 'template_tags', ['usage_count'])
    op.create_index('idx_tag_featured', 'template_tags', ['is_featured'])
    
    # 6. 插入初始数据
    # 插入默认分类
    categories_data = [
        ('创作', '内容创作相关模板', 'edit', '#1890ff', 1),
        ('编程', '编程开发相关模板', 'code', '#52c41a', 2),
        ('分析', '数据分析相关模板', 'bar-chart', '#faad14', 3),
        ('翻译', '语言翻译相关模板', 'global', '#722ed1', 4),
        ('总结', '内容总结相关模板', 'file-text', '#fa8c16', 5),
        ('客服', '客户服务相关模板', 'customer-service', '#13c2c2', 6),
        ('教育', '教育培训相关模板', 'book', '#eb2f96', 7),
        ('营销', '市场营销相关模板', 'rocket', '#f5222d', 8),
        ('其他', '其他类型模板', 'appstore', '#666666', 99)
    ]
    
    # 插入分类数据
    for name, desc, icon, color, sort_order in categories_data:
        op.execute(f"""
            INSERT INTO template_categories (id, name, description, icon, color, sort_order, is_active)
            VALUES (gen_random_uuid(), '{name}', '{desc}', '{icon}', '{color}', {sort_order}, true)
        """)
    
    # 插入默认标签
    tags_data = [
        ('AI助手', '人工智能助手相关', '#1890ff', True),
        ('文案写作', '文案创作相关', '#52c41a', True),
        ('代码生成', '代码生成相关', '#faad14', True),
        ('数据分析', '数据分析相关', '#722ed1', True),
        ('客户服务', '客户服务相关', '#fa8c16', True),
        ('教育培训', '教育培训相关', '#13c2c2', True),
        ('创意设计', '创意设计相关', '#eb2f96', False),
        ('商务沟通', '商务沟通相关', '#f5222d', False),
        ('技术文档', '技术文档相关', '#096dd9', False),
        ('产品介绍', '产品介绍相关', '#389e0d', False)
    ]
    
    # 插入标签数据
    for name, desc, color, is_featured in tags_data:
        op.execute(f"""
            INSERT INTO template_tags (id, name, description, color, is_featured, usage_count)
            VALUES (gen_random_uuid(), '{name}', '{desc}', '{color}', {is_featured}, 0)
        """)

def downgrade():
    """降级数据库结构"""
    
    # 删除索引
    op.drop_index('idx_tag_featured', 'template_tags')
    op.drop_index('idx_tag_usage', 'template_tags')
    op.drop_index('idx_tag_name', 'template_tags')
    
    op.drop_index('idx_category_sort', 'template_categories')
    op.drop_index('idx_category_active', 'template_categories')
    op.drop_index('idx_category_parent', 'template_categories')
    op.drop_index('idx_category_name', 'template_categories')
    
    op.drop_index('idx_collection_name', 'template_collections')
    op.drop_index('idx_collection_template', 'template_collections')
    op.drop_index('idx_collection_user', 'template_collections')
    
    op.drop_index('idx_template_language', 'templates')
    op.drop_index('idx_template_verified', 'templates')
    op.drop_index('idx_template_usage', 'templates')
    op.drop_index('idx_template_rating', 'templates')
    op.drop_index('idx_template_featured', 'templates')
    op.drop_index('idx_template_public', 'templates')
    op.drop_index('idx_template_difficulty', 'templates')
    op.drop_index('idx_template_industry', 'templates')
    op.drop_index('idx_template_tags', 'templates')
    op.drop_index('idx_template_category', 'templates')
    
    # 删除表
    op.drop_table('template_tags')
    op.drop_table('template_categories')
    op.drop_table('template_collections')
    
    # 删除外键约束
    op.drop_constraint('fk_templates_parent_id', 'templates', type_='foreignkey')
    
    # 删除新增字段
    op.drop_column('templates', 'parent_id')
    op.drop_column('templates', 'version')
    op.drop_column('templates', 'metadata')
    op.drop_column('templates', 'use_case')
    op.drop_column('templates', 'industry')
    op.drop_column('templates', 'language')
    op.drop_column('templates', 'difficulty_level')
    op.drop_column('templates', 'is_verified')
    op.drop_column('templates', 'rating_count')
