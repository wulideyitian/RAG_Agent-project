"""
RAG API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from core.api.schemas.response import ChatResponse, APIResponse
from app.utils.logger_handler import logger

router = APIRouter(prefix="/api/rag", tags=["RAG 检索"])


class RAGQuery(BaseModel):
    """RAG 查询请求"""
    query: str = Field(..., description="检索问题")
    k: int = Field(default=3, description="返回文档数量")


@router.post("/query", response_model=ChatResponse)
async def rag_query(request: RAGQuery):
    """
    RAG 检索接口
    """
    try:
        from core.rag.generator import RAGGenerator
        
        generator = RAGGenerator()
        response = await generator.rag_summarize(request.query)
        
        return ChatResponse(
            response=response,
            sources=[]
        )
        
    except Exception as e:
        logger.error(f"RAG 检索异常：{str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=APIResponse)
async def rag_health():
    """
    RAG 服务健康检查
    """
    try:
        from core.rag.vector_store import VectorStoreService
        
        # 尝试初始化向量库
        vs = VectorStoreService()
        
        return APIResponse(
            success=True,
            message="RAG 服务正常",
            data={"status": "healthy"}
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"RAG 服务异常：{str(e)}",
            error=str(e)
        )
