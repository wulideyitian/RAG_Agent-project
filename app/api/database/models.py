"""
数据库 ORM 模型定义
包含用户记忆、对话历史、记忆检索日志等模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Enum, JSON, Index
from sqlalchemy.sql import func
from datetime import datetime
import enum

# 延迟导入 Base，避免初始化时依赖 db_manager
Base = None

def get_base():
    """延迟获取 Base 类"""
    global Base
    if Base is None:
        from .db_connection import db_manager
        Base = db_manager.Base
    return Base


class RoleEnum(str, enum.Enum):
    """对话角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"


class UserMemory(get_base()):
    """用户长期记忆表"""
    __tablename__ = "user_memories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), unique=True, nullable=False, index=True, comment="用户唯一标识")
    
    # 记忆内容字段
    mentioned_models = Column(JSON, default=list, comment="提到的笔记本型号列表")
    budget = Column(String(50), nullable=True, comment="预算范围")
    usage_scenario = Column(String(100), nullable=True, comment="使用场景")
    location = Column(String(100), nullable=True, comment="地理位置")
    preferences = Column(JSON, default=dict, comment="用户偏好配置")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(
        DateTime, 
        default=datetime.now, 
        onupdate=datetime.now, 
        comment="更新时间"
    )
    
    def __repr__(self):
        return f"<UserMemory(user_id='{self.user_id}')>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "mentioned_models": self.mentioned_models or [],
            "budget": self.budget,
            "usage_scenario": self.usage_scenario,
            "location": self.location,
            "preferences": self.preferences or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ConversationHistory(get_base()):
    """对话历史记录表"""
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True, comment="用户 ID")
    session_id = Column(String(64), nullable=False, index=True, comment="会话 ID")
    
    # 对话内容
    role = Column(Enum(RoleEnum), nullable=False, comment="角色")
    content = Column(Text, nullable=False, comment="对话内容")
    message_type = Column(String(50), default="normal", comment="消息类型（normal/tool_call）")
    meta_data = Column(JSON, default=dict, comment="元数据（工具调用信息等）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 索引优化查询
    __table_args__ = (
        Index("idx_user_session", "user_id", "session_id"),
        Index("idx_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<ConversationHistory(id={self.id}, role='{self.role}', session_id='{self.session_id}')>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "role": self.role.value,
            "content": self.content,
            "message_type": self.message_type,
            "metadata": self.metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MemoryRetrievalLog(get_base()):
    """记忆检索记录表"""
    __tablename__ = "memory_retrieval_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True, comment="用户 ID")
    
    # 检索信息
    query_keywords = Column(String(255), nullable=True, comment="检索关键词")
    retrieved_memory_ids = Column(JSON, default=list, comment="检索到的记忆 ID 列表")
    retrieval_score = Column(Float, nullable=True, comment="检索评分")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    def __repr__(self):
        return f"<MemoryRetrievalLog(id={self.id}, user_id='{self.user_id}')>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "query_keywords": self.query_keywords,
            "retrieved_memory_ids": self.retrieved_memory_ids or [],
            "retrieval_score": self.retrieval_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
