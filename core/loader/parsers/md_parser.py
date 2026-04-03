"""
Markdown 文件解析器
"""
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from app.utils.logger_handler import logger
from core.preprocessing.text_cleaner import TextCleaner


class MarkdownParser:
    """Markdown 文件解析器"""
    
    def __init__(self):
        self.text_cleaner = TextCleaner()
    
    def parse(self, filepath: str) -> List[Document]:
        """
        解析 Markdown 文件
        :param filepath: 文件路径
        :return: Document 列表
        """
        try:
            loader = UnstructuredMarkdownLoader(filepath)
            documents = loader.load()
            
            if not documents:
                return []
            
            # 清理文本
            cleaned_content = self.text_cleaner.clean(
                documents[0].page_content, 
                'md'
            )
            
            doc = Document(
                page_content=cleaned_content, 
                metadata={"source": filepath}
            )
            
            logger.info(f"Markdown 文件{filepath}解析成功")
            return [doc]
            
        except Exception as e:
            logger.error(f"解析 Markdown 文件{filepath}失败：{str(e)}")
            raise Exception(f"Markdown 解析失败：{str(e)}")
