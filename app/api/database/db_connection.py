"""
数据库连接管理模块
提供 SQLAlchemy 数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator
import yaml
from pathlib import Path


class DatabaseManager:
    """数据库管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_config()
            self._create_engine()
            self.SessionLocal = sessionmaker(
                autocommit=False, 
                autoflush=False, 
                bind=self.engine
            )
            self.Base = declarative_base()
            self._initialized = True
    
    def _load_config(self):
        """加载数据库配置文件"""
        # 使用绝对路径，从项目根目录查找
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / 'config' / 'database.yml',
            Path.cwd() / 'config' / 'database.yml',
            Path(__file__).parent.parent.parent / 'config' / 'database.yml',
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
        
        db_config = config['database']
        self.host = db_config['host']
        self.port = db_config['port']
        self.username = db_config['username']
        self.password = db_config['password']
        self.database_name = db_config['database_name']
        self.charset = db_config.get('charset', 'utf8mb4')
        self.pool_size = db_config.get('pool_size', 10)
        self.max_overflow = db_config.get('max_overflow', 20)
        self.pool_pre_ping = db_config.get('pool_pre_ping', True)
    
    def _create_engine(self):
        """创建数据库引擎"""
        # 先连接到 MySQL 服务器（不指定具体数据库），用于建库
        connection_url_base = (
            f"mysql+pymysql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/"
            f"?charset={self.charset}"
        )
        
        # 尝试连接并检查数据库是否存在
        try:
            from sqlalchemy import text
            temp_engine = create_engine(connection_url_base)
            with temp_engine.connect() as conn:
                # 检查数据库是否存在
                result = conn.execute(
                    text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{self.database_name}'")
                )
                db_exists = result.fetchone() is not None
            
            temp_engine.dispose()
            
            if not db_exists:
                # 数据库不存在，抛出友好提示
                raise RuntimeError(
                    f"数据库 '{self.database_name}' 不存在。\n"
                    f"请先运行初始化脚本：python scripts/init_database.py"
                )
        except Exception as e:
            if "database" in str(e).lower() and "not exist" in str(e).lower():
                raise
            # 其他错误（如连接失败）也给出提示
            raise RuntimeError(
                f"无法连接到 MySQL 服务器：{e}\n"
                f"请检查:\n"
                f"1. MySQL 服务是否已启动\n"
                f"2. config/database.yml 配置是否正确\n"
                f"3. 用户名密码是否正确"
            )
        
        # 数据库存在，创建正式的连接
        connection_url = (
            f"mysql+pymysql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database_name}"
            f"?charset={self.charset}"
        )
        
        self.engine = create_engine(
            connection_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_pre_ping=self.pool_pre_ping,
            echo=False,  # 生产环境关闭 SQL 日志
            pool_recycle=3600,  # 1 小时回收连接
        )
    
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """创建所有表（仅用于初始化）"""
        self.Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """删除所有表（仅用于测试）"""
        self.Base.metadata.drop_all(bind=self.engine)


# 全局数据库实例
db_manager = DatabaseManager()

# 导出 Base 供模型使用
Base = db_manager.Base


def get_db() -> Generator[Session, None, None]:
    """依赖注入：获取数据库会话"""
    yield from db_manager.get_session()
