"""
API 请求模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """聊天请求模型"""
    query: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    stream: bool = Field(default=False, description="是否启用流式响应")


class FileUploadRequest(BaseModel):
    """文件上传请求模型"""
    filename: str = Field(..., min_length=1, description="文件名")
    file_type: str = Field(..., pattern=r"^(pdf|txt|docx|md)$", description="文件类型")
