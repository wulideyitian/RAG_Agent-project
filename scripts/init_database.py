"""
数据库初始化脚本
用于创建数据库和所有表
独立于 db_manager，避免循环依赖
"""
import pymysql
import yaml
from pathlib import Path


def load_db_config():
    """直接加载配置文件，不依赖 db_manager"""
    # 使用多种可能路径查找配置文件
    possible_paths = [
        Path(__file__).parent.parent / 'config' / 'database.yml',
        Path.cwd() / 'config' / 'database.yml',
        Path(__file__).parent / 'config' / 'database.yml',
    ]
    
    config_path = None
    for path in possible_paths:
        if path.exists():
            config_path = path
            break
    
    if not config_path:
        raise FileNotFoundError(
            "无法找到 database.yml 配置文件，请在 config/ 目录下创建该文件"
        )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config['database']


def create_database():
    """创建数据库（如果不存在）"""
    # 直接加载配置，不依赖 db_manager
    db_config = load_db_config()
    
    # 连接到 MySQL 服务器（不指定数据库）
    # 注意：pymysql 的 password 参数需要字符串，会自动处理编码
    connection = pymysql.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['username'],
        password=str(db_config['password']),  # 确保是字符串
        charset='utf8mb4',
    )
    
    try:
        with connection.cursor() as cursor:
            # 创建数据库
            sql = f"""
                CREATE DATABASE IF NOT EXISTS {db_config['database_name']}
                DEFAULT CHARACTER SET {db_config.get('charset', 'utf8mb4')}
                DEFAULT COLLATE utf8mb4_unicode_ci
            """
            cursor.execute(sql)
            print(f"Database '{db_config['database_name']}' created or already exists.")
        
        connection.commit()
    finally:
        connection.close()


def init_tables():
    """创建所有表"""
    print("Creating tables...")
    
    # 导入 ORM 模型并创建表
    from sqlalchemy import create_engine
    from app.api.database.models import Base
    
    # 加载配置创建临时引擎
    db_config = load_db_config()
    connection_url = (
        f"mysql+pymysql://{db_config['username']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['database_name']}"
        f"?charset={db_config.get('charset', 'utf8mb4')}"
    )
    
    engine = create_engine(connection_url)
    Base.metadata.create_all(bind=engine)
    
    print("All tables created successfully!")


if __name__ == "__main__":
    print("Starting database initialization...")
    
    # 1. 创建数据库
    create_database()
    
    # 2. 创建所有表
    init_tables()
    
    print("Database initialization completed!")
