# models package (Pydantic schemas)
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatRequest(BaseModel):
    """聊天请求模型"""
    query: str = Field(..., description="用户提问内容", min_length=1, max_length=5000)
    stream: bool = Field(default=True, description="是否使用流式响应")
    context: Optional[dict] = Field(default=None, description="上下文信息")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    success: bool = Field(default=True, description="请求是否成功")
    data: Optional[str] = Field(default=None, description="回答内容")
    message: Optional[str] = Field(default=None, description="错误信息或附加消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")


class FileUploadRequest(BaseModel):
    """文件上传请求模型（用于文档描述）"""
    description: Optional[str] = Field(default=None, description="文件描述", max_length=500)


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    success: bool = Field(default=True, description="上传是否成功")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件存储路径")
    file_size: int = Field(..., description="文件大小（字节）")
    message: Optional[str] = Field(default=None, description="附加消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="上传时间戳")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    message: str = Field(..., description="消息")
    version: Optional[str] = Field(default="1.0.0", description="API 版本")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间戳")


class RootResponse(BaseModel):
    """根路径响应模型"""
    message: str = Field(..., description="欢迎消息")
    docs_url: str = Field(default="/docs", description="API 文档地址")
    version: str = Field(default="1.0.0", description="API 版本")
