"""
统一文档加载器
自动识别文件格式并调用对应的 Parser
"""
import os
from typing import Union
from app.utils.logger_handler import logger
from langchain_core.documents import Document


class UnifiedDocumentLoader:
    """
    统一文档加载器：自动识别文件格式并调用对应的 Parser
    支持入参：文件路径或二进制流
    """
    
    def __init__(self):
        from core.loader.parsers.pdf_parser import PDFParser
        from core.loader.parsers.docx_parser import DOCXParser
        from core.loader.parsers.txt_parser import TXTParser
        from core.loader.parsers.md_parser import MarkdownParser
        
        self.parsers = {
            'pdf': PDFParser(),
            'txt': TXTParser(),
            'docx': DOCXParser(),
            'doc': DOCXParser(),  # DOC 也尝试用 DOCX Parser
            'md': MarkdownParser(),
            'markdown': MarkdownParser(),
        }
    
    def _detect_file_type(self, filepath: str) -> str:
        """
        根据文件扩展名检测文件类型
        :param filepath: 文件路径
        :return: 文件类型标识
        """
        ext = os.path.splitext(filepath)[1].lower().lstrip('.')
        if ext in self.parsers:
            return ext
        
        logger.warning(f"无法识别文件类型：{filepath}，使用扩展名{ext}")
        return ext
    
    def load_from_path(self, filepath: str) -> dict:
        """
        从文件路径加载文档
        :param filepath: 文件路径
        :return: {"text": 纯文本内容，"file_type": 格式类型，"status": 解析状态，"error_msg": 错误信息}
        """
        try:
            file_type = self._detect_file_type(filepath)
            
            if file_type not in self.parsers:
                return {
                    "text": "",
                    "file_type": file_type,
                    "status": "error",
                    "error_msg": f"不支持的文件类型：{file_type}"
                }
            
            parser_func = self.parsers[file_type]
            documents = parser_func.parse(filepath)
            
            if not documents:
                return {
                    "text": "",
                    "file_type": file_type,
                    "status": "warning",
                    "error_msg": "未提取到有效内容"
                }
            
            full_text = "\n\n".join([doc.page_content for doc in documents])
            
            return {
                "text": full_text,
                "file_type": file_type,
                "status": "success",
                "error_msg": ""
            }
            
        except Exception as e:
            logger.error(f"加载文档失败：{str(e)}")
            return {
                "text": "",
                "file_type": "unknown",
                "status": "error",
                "error_msg": f"加载失败：{str(e)}"
            }
    
    def load_from_binary(self, binary_data: bytes, file_type: str) -> dict:
        """
        从二进制流加载文档（临时文件方式）
        :param binary_data: 文件二进制数据
        :param file_type: 文件类型标识
        :return: {"text": 纯文本内容，"file_type": 格式类型，"status": 解析状态，"error_msg": 错误信息}
        """
        import tempfile
        
        try:
            suffix = f".{file_type}"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                tmp_file.write(binary_data)
                tmp_path = tmp_file.name
            
            try:
                result = self.load_from_path(tmp_path)
                return result
            finally:
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"从二进制流加载文档失败：{str(e)}")
            return {
                "text": "",
                "file_type": file_type,
                "status": "error",
                "error_msg": f"从二进制流加载失败：{str(e)}"
            }
