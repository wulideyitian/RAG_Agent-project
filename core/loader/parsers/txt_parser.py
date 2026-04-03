"""
TXT 文件解析器
"""
import chardet
from typing import List
from langchain_core.documents import Document
from app.utils.logger_handler import logger
from core.preprocessing.text_cleaner import TextCleaner


class TXTParser:
    """TXT 文件解析器（带编码检测）"""
    
    def __init__(self):
        self.text_cleaner = TextCleaner()
    
    def _detect_encoding(self, filepath: str) -> str:
        """检测文件编码"""
        try:
            with open(filepath, 'rb') as f:
                raw_data = f.read(1024 * 4)
                result = chardet.detect(raw_data)
                encoding = result['encoding'] if result['encoding'] else 'utf-8'
                confidence = result['confidence'] if result['confidence'] else 0
                
                if confidence < 0.7:
                    logger.warning(f"文件{filepath}编码检测结果置信度较低：{confidence}")
                
                return encoding
        except Exception as e:
            logger.error(f"检测文件{filepath}编码失败：{str(e)}")
            return 'utf-8'
    
    def parse(self, filepath: str) -> List[Document]:
        """
        解析 TXT 文件
        :param filepath: 文件路径
        :return: Document 列表
        """
        try:
            encoding = self._detect_encoding(filepath)
            
            with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            
            # 检查是否为空文件
            if not content or not content.strip():
                logger.warning(f"TXT 文件{filepath}为空文件")
                return []
            
            # 清理文本
            content = self.text_cleaner.clean(content, 'txt')
            
            doc = Document(page_content=content, metadata={"source": filepath})
            
            logger.info(f"TXT 文件{filepath}解析成功")
            return [doc]
            
        except Exception as e:
            logger.error(f"解析 TXT 文件{filepath}失败：{str(e)}")
            raise Exception(f"TXT 解析失败：{str(e)}")
