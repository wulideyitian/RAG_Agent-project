"""
文件处理业务服务
封装文件上传、解析、处理等业务逻辑
"""
import os
import shutil
from datetime import datetime
from typing import Union, BinaryIO
from fastapi import UploadFile
from app.utils.file_handler import get_file_md5_hex
from core.loader.document_loader import UnifiedDocumentLoader
from app.utils.logger_handler import logger
from app.utils.path_tool import get_project_root


class FileService:
    """
    文件处理服务
    提供文件解析、MD5 计算等功能
    """
    
    def __init__(self):
        self.doc_loader = UnifiedDocumentLoader()
    
    def parse_file(self, filepath: str) -> dict:
        """
        解析文件内容
        :param filepath: 文件路径
        :return: {
            "text": 纯文本内容，
            "file_type": 格式类型，
            "status": 解析状态，
            "error_msg": 错误信息
        }
        """
        result = self.doc_loader.load_from_path(filepath)
        return result
    
    def parse_binary(self, binary_data: bytes, file_type: str) -> dict:
        """
        解析二进制流文件
        :param binary_data: 文件二进制数据
        :param file_type: 文件类型（pdf, txt, docx, md 等）
        :return: {
            "text": 纯文本内容，
            "file_type": 格式类型，
            "status": 解析状态，
            "error_msg": 错误信息
        }
        """
        result = self.doc_loader.load_from_binary(binary_data, file_type)
        return result
    
    def get_file_md5(self, filepath: str) -> str:
        """
        获取文件的 MD5 值
        :param filepath: 文件路径
        :return: MD5 十六进制字符串
        """
        return get_file_md5_hex(filepath)
    
    def detect_file_type(self, filepath: str) -> str:
        """
        检测文件类型
        :param filepath: 文件路径
        :return: 文件类型标识
        """
        # 使用统一加载器的内部方法检测
        return self.doc_loader._detect_file_type(filepath)
    
    async def save_uploaded_file(self, file: UploadFile, description: str = None) -> dict:
        """
        保存上传的文件
        :param file: FastAPI UploadFile 对象
        :param description: 文件描述
        :return: {
            "success": 是否成功，
            "filename": 文件名，
            "file_path": 存储路径，
            "file_size": 文件大小，
            "message": 附加消息
        }
        """
        try:
            # 获取项目根目录
            project_root = get_project_root()
            upload_dir = os.path.join(project_root, "data", "uploads")
            
            # 确保上传目录存在
            os.makedirs(upload_dir, exist_ok=True)
            
            # 生成唯一文件名（使用时间戳 + 原文件名）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_filename = file.filename or "unnamed"
            safe_filename = f"{timestamp}_{original_filename}"
            file_path = os.path.join(upload_dir, safe_filename)
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            logger.info(f"文件上传成功：{safe_filename}, 大小：{file_size} bytes")
            
            return {
                "success": True,
                "filename": safe_filename,
                "file_path": file_path,
                "file_size": file_size,
                "message": description or "文件上传成功"
            }
            
        except Exception as e:
            logger.error(f"文件上传失败：{str(e)}")
            raise
