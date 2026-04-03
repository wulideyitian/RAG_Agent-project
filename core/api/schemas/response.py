"""
API 响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class APIResponse(BaseModel):
    """通用 API 响应"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    error: Optional[str] = Field(None, description="错误信息")


class ChatRequest(BaseModel):
    """聊天请求"""
    query: str = Field(..., description="用户问题")
    stream: bool = Field(False, description="是否流式响应")


class ChatResponse(BaseModel):
    """聊天响应"""
    response: str = Field(..., description="AI 回答")
    sources: Optional[list] = Field(None, description="参考来源")


class FileUploadRequest(BaseModel):
    """文件上传请求"""
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
