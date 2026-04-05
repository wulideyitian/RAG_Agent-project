"""  
API 请求模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import uuid


class ChatRequest(BaseModel):
    """聊天请求模型"""
    query: Optional[str] = Field(default=None, min_length=1, max_length=2000, description="用户问题（如果不提供 messages 字段）")
    messages: Optional[List[Dict[str, str]]] = Field(default=None, description="完整的消息列表（推荐方式）")
    stream: bool = Field(default=False, description="是否启用流式响应")
    
    def __init__(self, **data):
        # 验证：query 和 messages 至少提供一个
        if not data.get('query') and not data.get('messages'):
            raise ValueError("必须提供 query 或 messages 字段")
        
        super().__init__(**data)


class FileUploadRequest(BaseModel):
    """文件上传请求模型"""
    filename: str = Field(..., min_length=1, description="文件名")
    file_type: str = Field(..., pattern=r"^(pdf|txt|docx|md)$", description="文件类型")
