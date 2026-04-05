"""
聊天 API 路由
"""
from fastapi import APIRouter, HTTPException
from core.api.schemas.request import ChatRequest
from core.api.schemas.response import ChatResponse, APIResponse
from app.utils.logger_handler import logger
from typing import List, Dict, Optional

router = APIRouter(prefix="/api/chat", tags=["聊天"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口（非流式）
    支持两种方式：
    1. 提供 messages 数组（推荐）：前端维护完整的对话历史
    2. 仅提供 query：向后兼容旧接口
    """
    try:
        from app.service.agent_service import AgentService
        
        agent_service = AgentService()
        
        if request.stream:
            # 流式响应暂不实现
            raise HTTPException(status_code=400, detail="流式响应暂未支持")
        
        # 构建消息列表
        if request.messages:
            # 使用前端提供的完整消息列表
            messages = request.messages
        else:
            # 向后兼容：仅使用 query 字段
            messages = [{"role": "user", "content": request.query}]
        
        # 执行对话
        response = agent_service.execute(
            messages=messages
        )
        
        return ChatResponse(
            response=response,
            sources=[]
        )
        
    except Exception as e:
        logger.error(f"聊天接口异常：{str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
