"""
聊天 API 路由
"""
from fastapi import APIRouter, HTTPException
from core.api.schemas.request import ChatRequest
from core.api.schemas.response import ChatResponse, APIResponse
from app.utils.logger_handler import logger

router = APIRouter(prefix="/api/chat", tags=["聊天"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口（非流式）
    """
    try:
        from core.agent.react_agent import ReactAgent
        
        agent = ReactAgent()
        
        if request.stream:
            # 流式响应暂不实现
            raise HTTPException(status_code=400, detail="流式响应暂未支持")
        
        response = agent.execute(request.query)
        
        return ChatResponse(
            response=response,
            sources=[]
        )
        
    except Exception as e:
        logger.error(f"聊天接口异常：{str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
