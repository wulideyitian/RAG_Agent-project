"""
记忆管理服务
提供用户记忆的增删改查、检索和更新功能
"""
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
import uuid
from datetime import datetime

from app.api.database.db_connection import db_manager, get_db
from app.api.database.models import UserMemory, ConversationHistory, MemoryRetrievalLog, RoleEnum


class MemoryService:
    """记忆管理服务类"""
    
    def __init__(self, session: Session = None):
        self.session = session
    
    def __enter__(self):
        """上下文管理器：自动获取会话"""
        self._session_gen = get_db()
        self.session = next(self._session_gen)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器：自动关闭会话"""
        try:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            self._session_gen.close()
    
    # ========== 用户记忆管理 ==========
    
    def create_user_memory(
        self,
        user_id: str = None,
        mentioned_models: List[str] = None,
        budget: str = None,
        usage_scenario: str = None,
        location: str = None,
        preferences: Dict = None,
    ) -> UserMemory:
        """创建用户记忆记录"""
        if user_id is None:
            user_id = str(uuid.uuid4())
        
        memory = UserMemory(
            user_id=user_id,
            mentioned_models=mentioned_models or [],
            budget=budget,
            usage_scenario=usage_scenario,
            location=location,
            preferences=preferences or {},
        )
        
        self.session.add(memory)
        self.session.flush()  # 获取自增 ID
        
        return memory
    
    def get_user_memory(self, user_id: str) -> Optional[UserMemory]:
        """获取用户记忆"""
        return self.session.query(UserMemory).filter(
            UserMemory.user_id == user_id
        ).first()
    
    def update_user_memory(
        self,
        user_id: str,
        mentioned_models: List[str] = None,
        budget: str = None,
        usage_scenario: str = None,
        location: str = None,
        preferences: Dict = None,
    ) -> Optional[UserMemory]:
        """更新用户记忆（只更新提供的字段）"""
        memory = self.get_user_memory(user_id)
        
        if memory is None:
            return None
        
        # 只更新非空字段
        if mentioned_models is not None:
            # 合并列表，去重
            existing = memory.mentioned_models or []
            memory.mentioned_models = list(set(existing + mentioned_models))
        
        if budget is not None:
            memory.budget = budget
        
        if usage_scenario is not None:
            memory.usage_scenario = usage_scenario
        
        if location is not None:
            memory.location = location
        
        if preferences is not None:
            # 合并字典
            existing = memory.preferences or {}
            memory.preferences = {**existing, **preferences}
        
        # updated_at 会自动更新
        self.session.flush()
        
        return memory
    
    def upsert_user_memory(
        self,
        user_id: str,
        mentioned_models: List[str] = None,
        budget: str = None,
        usage_scenario: str = None,
        location: str = None,
        preferences: Dict = None,
    ) -> UserMemory:
        """如果用户存在则更新，否则创建"""
        memory = self.get_user_memory(user_id)
        
        if memory:
            return self.update_user_memory(
                user_id=user_id,
                mentioned_models=mentioned_models,
                budget=budget,
                usage_scenario=usage_scenario,
                location=location,
                preferences=preferences,
            )
        else:
            return self.create_user_memory(
                user_id=user_id,
                mentioned_models=mentioned_models,
                budget=budget,
                usage_scenario=usage_scenario,
                location=location,
                preferences=preferences,
            )
    
    def delete_user_memory(self, user_id: str) -> bool:
        """删除用户记忆"""
        memory = self.get_user_memory(user_id)
        if memory:
            self.session.delete(memory)
            return True
        return False
    
    def search_memories(
        self,
        keywords: str = None,
        user_id: str = None,
        limit: int = 10,
    ) -> List[UserMemory]:
        """搜索记忆（支持关键词和用户 ID 过滤）"""
        query = self.session.query(UserMemory)
        
        if user_id:
            query = query.filter(UserMemory.user_id == user_id)
        
        if keywords:
            # 模糊搜索多个字段
            conditions = [
                UserMemory.usage_scenario.like(f"%{keywords}%"),
                UserMemory.location.like(f"%{keywords}%"),
                UserMemory.budget.like(f"%{keywords}%"),
            ]
            
            # JSON 字段的搜索需要特殊处理（MySQL 5.7+）
            # 这里简化处理，在应用层过滤
            query = query.filter(or_(*conditions))
        
        results = query.limit(limit).all()
        
        # 应用层过滤 JSON 字段
        if keywords:
            filtered_results = []
            for memory in results:
                if any(keywords.lower() in model.lower() 
                      for model in (memory.mentioned_models or [])):
                    filtered_results.append(memory)
            results = filtered_results[:limit]
        
        return results
    
    # ========== 对话历史管理 ==========
    
    def add_conversation(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "normal",
        metadata: Dict = None,
    ) -> ConversationHistory:
        """添加对话记录"""
        conversation = ConversationHistory(
            user_id=user_id,
            session_id=session_id,
            role=RoleEnum(role),
            content=content,
            message_type=message_type,
            metadata=metadata or {},
        )
        
        self.session.add(conversation)
        self.session.flush()
        
        return conversation
    
    def get_conversation_history(
        self,
        user_id: str,
        session_id: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ConversationHistory]:
        """获取对话历史"""
        query = self.session.query(ConversationHistory).filter(
            ConversationHistory.user_id == user_id
        )
        
        if session_id:
            query = query.filter(ConversationHistory.session_id == session_id)
        
        results = query.order_by(
            ConversationHistory.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        # 按时间正序返回
        return list(reversed(results))
    
    def get_session_ids(self, user_id: str) -> List[str]:
        """获取用户的所有会话 ID"""
        results = self.session.query(
            ConversationHistory.session_id
        ).filter(
            ConversationHistory.user_id == user_id
        ).distinct().all()
        
        return [r.session_id for r in results]
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """删除指定会话的所有对话记录"""
        count = self.session.query(ConversationHistory).filter(
            ConversationHistory.user_id == user_id,
            ConversationHistory.session_id == session_id,
        ).delete()
        
        return count > 0
    
    def clear_all_conversations(self, user_id: str) -> int:
        """清空用户的所有对话记录"""
        count = self.session.query(ConversationHistory).filter(
            ConversationHistory.user_id == user_id
        ).delete()
        
        return count
    
    # ========== 记忆检索日志 ==========
    
    def log_retrieval(
        self,
        user_id: str,
        query_keywords: str,
        retrieved_memory_ids: List[int],
        retrieval_score: float = None,
    ) -> MemoryRetrievalLog:
        """记录记忆检索操作"""
        log = MemoryRetrievalLog(
            user_id=user_id,
            query_keywords=query_keywords,
            retrieved_memory_ids=retrieved_memory_ids,
            retrieval_score=retrieval_score,
        )
        
        self.session.add(log)
        self.session.flush()
        
        return log
    
    def get_retrieval_logs(
        self,
        user_id: str,
        limit: int = 20,
    ) -> List[MemoryRetrievalLog]:
        """获取用户的检索日志"""
        return self.session.query(MemoryRetrievalLog).filter(
            MemoryRetrievalLog.user_id == user_id
        ).order_by(
            MemoryRetrievalLog.created_at.desc()
        ).limit(limit).all()
    
    # ========== 高级功能 ==========
    
    def extract_and_update_memory(
        self,
        user_id: str,
        conversation_content: str,
        memory_updates: Dict[str, Any],
    ) -> UserMemory:
        """
        从对话中提取信息并更新记忆
        :param user_id: 用户 ID
        :param conversation_content: 对话内容
        :param memory_updates: 要更新的记忆字段
        :return: 更新后的记忆对象
        """
        return self.upsert_user_memory(
            user_id=user_id,
            **memory_updates,
        )
    
    def get_full_context(
        self,
        user_id: str,
        session_id: str = None,
        max_history_turns: int = 10,
    ) -> Dict:
        """
        获取完整的上下文信息（用户记忆 + 对话历史）
        :param user_id: 用户 ID
        :param session_id: 可选的会话 ID
        :param max_history_turns: 最大返回的历史对话轮数
        :return: 包含记忆和历史的字典
        """
        memory = self.get_user_memory(user_id)
        history = self.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=max_history_turns * 2,  # 每轮包含 user 和 assistant
        )
        
        return {
            "user_memory": memory.to_dict() if memory else None,
            "conversation_history": [h.to_dict() for h in history],
        }
