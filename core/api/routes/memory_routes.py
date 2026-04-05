"""
记忆管理 API 路由
提供用户记忆和对话历史的 HTTP 接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.database.db_connection import get_db
from app.service.memory_service import MemoryService
from app.api.database.models import UserMemory, ConversationHistory


router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/user/{user_id}")
def get_user_memory_api(
    user_id: str,
    db: Session = Depends(get_db),
):
    """获取用户记忆"""
    service = MemoryService(db)
    memory = service.get_user_memory(user_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="User memory not found")
    
    return {
        "success": True,
        "data": memory.to_dict(),
    }


@router.post("/user/{user_id}/update")
def update_user_memory_api(
    user_id: str,
    mentioned_models: Optional[List[str]] = None,
    budget: Optional[str] = None,
    usage_scenario: Optional[str] = None,
    location: Optional[str] = None,
    preferences: Optional[dict] = None,
    db: Session = Depends(get_db),
):
    """更新用户记忆"""
    service = MemoryService(db)
    
    updated_memory = service.update_user_memory(
        user_id=user_id,
        mentioned_models=mentioned_models,
        budget=budget,
        usage_scenario=usage_scenario,
        location=location,
        preferences=preferences,
    )
    
    if not updated_memory:
        # 如果用户不存在，则创建
        updated_memory = service.create_user_memory(
            user_id=user_id,
            mentioned_models=mentioned_models,
            budget=budget,
            usage_scenario=usage_scenario,
            location=location,
            preferences=preferences,
        )
    
    return {
        "success": True,
        "data": updated_memory.to_dict(),
    }


@router.delete("/user/{user_id}")
def delete_user_memory_api(
    user_id: str,
    db: Session = Depends(get_db),
):
    """删除用户记忆"""
    service = MemoryService(db)
    success = service.delete_user_memory(user_id)
    
    return {
        "success": success,
        "message": "User memory deleted" if success else "User memory not found",
    }


@router.get("/user/{user_id}/search")
def search_memories_api(
    user_id: str,
    keywords: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """搜索记忆"""
    service = MemoryService(db)
    memories = service.search_memories(
        keywords=keywords,
        user_id=user_id,
        limit=limit,
    )
    
    return {
        "success": True,
        "data": [m.to_dict() for m in memories],
        "count": len(memories),
    }


@router.get("/user/{user_id}/conversations")
def get_conversation_history_api(
    user_id: str,
    session_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """获取对话历史"""
    service = MemoryService(db)
    conversations = service.get_conversation_history(
        user_id=user_id,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )
    
    return {
        "success": True,
        "data": [c.to_dict() for c in conversations],
        "count": len(conversations),
    }


@router.get("/user/{user_id}/sessions")
def get_session_ids_api(
    user_id: str,
    db: Session = Depends(get_db),
):
    """获取用户的所有会话 ID"""
    service = MemoryService(db)
    session_ids = service.get_session_ids(user_id)
    
    return {
        "success": True,
        "data": session_ids,
        "count": len(session_ids),
    }


@router.delete("/user/{user_id}/session/{session_id}")
def delete_session_api(
    user_id: str,
    session_id: str,
    db: Session = Depends(get_db),
):
    """删除指定会话的对话记录"""
    service = MemoryService(db)
    success = service.delete_session(user_id, session_id)
    
    return {
        "success": success,
        "message": "Session deleted" if success else "Session not found",
    }


@router.get("/user/{user_id}/context")
def get_full_context_api(
    user_id: str,
    session_id: Optional[str] = None,
    max_history_turns: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """获取完整上下文（用户记忆 + 对话历史）"""
    service = MemoryService(db)
    context = service.get_full_context(
        user_id=user_id,
        session_id=session_id,
        max_history_turns=max_history_turns,
    )
    
    return {
        "success": True,
        "data": context,
    }
