# file_routers package
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
import json
from typing import Generator

from app.api.models import (
    ChatRequest,
    ChatResponse,
    FileUploadResponse,
    HealthResponse,
    RootResponse,
)
from app.service.agent_service import AgentService
from app.service.file_service import FileService

router = APIRouter(prefix="/api")

# 延迟初始化服务（避免启动时失败）
_agent_service: AgentService = None
file_service = FileService()


def get_agent_service() -> AgentService:
    """获取或创建 AgentService 实例（延迟初始化）"""
    global _agent_service
    if _agent_service is None:
        try:
            _agent_service = AgentService()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Agent 服务初始化失败：{str(e)}"
            )
    return _agent_service


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "服务运行正常"}


@router.get("/", response_model=RootResponse)
async def root():
    """根路由"""
    return {
        "message": "欢迎使用笔记本智能问答助手 API",
        "docs_url": "/docs",
        "version": "1.0.0"
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    智能问答接口
    
    - **query**: 用户提问内容（必填，1-5000 字符）
    - **stream**: 是否使用流式响应（可选，默认 True）
    - **context**: 上下文信息（可选）
    
    返回完整的 JSON 响应或流式响应
    """
    try:
        if request.stream:
            # 流式响应
            return StreamingResponse(
                generate_chat_stream(request.query),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # 非流式响应
            service = get_agent_service()
            response = service.execute(request.query)
            return ChatResponse(
                success=True,
                data=response,
                message="回答成功"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理请求时发生错误：{str(e)}"
        )


def generate_chat_stream(query: str) -> Generator[str, None, None]:
    """生成流式响应数据"""
    service = get_agent_service()
    for chunk in service.execute_stream(query):
        # SSE 格式：data: {...}\n\n
        data = json.dumps({
            "success": True,
            "data": chunk,
            "type": "chunk"
        }, ensure_ascii=False)
        yield f"data: {data}\n\n"
    
    # 发送结束标记
    yield "data: [DONE]\n\n"


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="要上传的文件"),
    description: str = Form(default=None, max_length=500, description="文件描述")
):
    """
    文件上传接口
    
    - **file**: 要上传的文件（必填）
    - **description**: 文件描述（可选，最大 500 字符）
    
    支持多种文件格式，上传后会自动保存到指定目录
    """
    try:
        result = await file_service.save_uploaded_file(file, description)
        return FileUploadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败：{str(e)}"
        )
