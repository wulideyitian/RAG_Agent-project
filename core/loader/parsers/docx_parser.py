"""
Word 文件解析器
"""
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders.word_document import Docx2txtLoader
from app.utils.logger_handler import logger
from core.preprocessing.text_cleaner import TextCleaner


class DOCXParser:
    """Word 文件解析器（仅提取纯文本段落）"""
    
    def __init__(self):
        self.text_cleaner = TextCleaner()
    
    def parse(self, filepath: str) -> List[Document]:
        """
        解析 Word 文件
        :param filepath: 文件路径
        :return: Document 列表
        """
        try:
            loader = Docx2txtLoader(filepath)
            documents = loader.load()
            
            if not documents:
                return []
            
            # 清理文本
            cleaned_content = self.text_cleaner.clean(
                documents[0].page_content, 
                'docx'
            )
            
            doc = Document(
                page_content=cleaned_content, 
                metadata={"source": filepath}
            )
            
            logger.info(f"Word 文件{filepath}解析成功")
            return [doc]
            
        except Exception as e:
            logger.error(f"解析 Word 文件{filepath}失败：{str(e)}")
            raise Exception(f"Word 解析失败：{str(e)}")
