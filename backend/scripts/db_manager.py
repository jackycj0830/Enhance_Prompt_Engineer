"""
数据库管理脚本
"""

import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from config.database import engine, SessionLocal, check_db_connection, check_redis_connection
from app.models import Base
import subprocess

def create_database():
    """创建数据库表"""
    print("🏗️  创建数据库表...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功")
        return True
    except Exception as e:
        print(f"❌ 创建数据库表失败: {e}")
        return False

def drop_database():
    """删除数据库表"""
    print("🗑️  删除数据库表...")
    try:
        Base.metadata.drop_all(bind=engine)
        print("✅ 数据库表删除成功")
        return True
    except Exception as e:
        print(f"❌ 删除数据库表失败: {e}")
        return False

def reset_database():
    """重置数据库"""
    print("🔄 重置数据库...")
    if drop_database() and create_database():
        print("✅ 数据库重置成功")
        return True
    return False

def run_migrations():
    """运行数据库迁移"""
    print("🚀 运行数据库迁移...")
    try:
        # 运行Alembic迁移
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 数据库迁移成功")
            print(result.stdout)
            return True
        else:
            print("❌ 数据库迁移失败")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ 运行迁移时出错: {e}")
        return False

def create_migration(message: str):
    """创建新的迁移文件"""
    print(f"📝 创建迁移: {message}")
    try:
        result = subprocess.run(
            ["python", "-m", "alembic", "revision", "--autogenerate", "-m", message],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 迁移文件创建成功")
            print(result.stdout)
            return True
        else:
            print("❌ 创建迁移文件失败")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ 创建迁移时出错: {e}")
        return False

def check_connections():
    """检查数据库连接"""
    print("🔍 检查数据库连接...")
    
    # 检查PostgreSQL连接
    if check_db_connection():
        print("✅ PostgreSQL 连接正常")
    else:
        print("❌ PostgreSQL 连接失败")
        return False
    
    # 检查Redis连接
    if check_redis_connection():
        print("✅ Redis 连接正常")
    else:
        print("❌ Redis 连接失败")
        return False
    
    return True

def show_database_info():
    """显示数据库信息"""
    print("📊 数据库信息:")
    
    db = SessionLocal()
    try:
        # 获取表信息
        result = db.execute(text("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """))
        
        tables = result.fetchall()
        if tables:
            print("\n📋 数据表:")
            for table_name, column_count in tables:
                # 获取记录数
                count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                record_count = count_result.scalar()
                print(f"   - {table_name}: {column_count} 列, {record_count} 条记录")
        else:
            print("   没有找到数据表")
            
        # 获取数据库大小
        size_result = db.execute(text("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as size;
        """))
        db_size = size_result.scalar()
        print(f"\n💾 数据库大小: {db_size}")
        
    except Exception as e:
        print(f"❌ 获取数据库信息失败: {e}")
    finally:
        db.close()

def seed_test_data():
    """生成测试数据"""
    print("🌱 生成测试数据...")
    try:
        from scripts.seed_data import main as seed_main
        seed_main()
        return True
    except Exception as e:
        print(f"❌ 生成测试数据失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库管理工具")
    parser.add_argument("command", choices=[
        "create", "drop", "reset", "migrate", "check", "info", "seed", "new-migration"
    ], help="要执行的命令")
    parser.add_argument("-m", "--message", help="迁移消息 (用于 new-migration 命令)")
    
    args = parser.parse_args()
    
    print("🗄️  Enhance Prompt Engineer 数据库管理工具")
    print("=" * 50)
    
    if args.command == "create":
        create_database()
    elif args.command == "drop":
        confirm = input("⚠️  确定要删除所有数据表吗? (y/N): ")
        if confirm.lower() == 'y':
            drop_database()
        else:
            print("操作已取消")
    elif args.command == "reset":
        confirm = input("⚠️  确定要重置数据库吗? 这将删除所有数据! (y/N): ")
        if confirm.lower() == 'y':
            reset_database()
        else:
            print("操作已取消")
    elif args.command == "migrate":
        run_migrations()
    elif args.command == "check":
        check_connections()
    elif args.command == "info":
        show_database_info()
    elif args.command == "seed":
        seed_test_data()
    elif args.command == "new-migration":
        if not args.message:
            print("❌ 请提供迁移消息 (-m 参数)")
            return
        create_migration(args.message)
    
    print("\n✨ 操作完成")

if __name__ == "__main__":
    main()
