"""
PDF 文件解析器（增强版 - 支持版式清理）
"""
import re
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from app.utils.logger_handler import logger
from core.preprocessing.pdf_layout_cleaner import PDFLayoutCleaner


class PDFParser:
    """PDF 文件解析器（增强版 - 集成版式清理）"""
    
    def __init__(self, enable_layout_cleaning: bool = True):
        """
        :param enable_layout_cleaning: 是否启用版式清理
        """
        self.enable_layout_cleaning = enable_layout_cleaning
        if enable_layout_cleaning:
            self.layout_cleaner = PDFLayoutCleaner()
            logger.info("PDF 版式清理已启用")
    
    def parse(self, filepath: str, passwd=None) -> List[Document]:
        """
        解析 PDF 文件
        :param filepath: 文件路径
        :param passwd: 密码（可选）
        :return: Document 列表
        """
        try:
            loader = PyPDFLoader(filepath, passwd)
            documents = loader.load()
            
            if not documents:
                logger.warning(f"PDF 文件{filepath}未解析到内容")
                return []
            
            # 如果启用了版式清理，进行深度清理
            if self.enable_layout_cleaning:
                return self._parse_with_layout_cleaning(documents, filepath)
            else:
                # 仅做基础的重复页眉页脚过滤
                return self._parse_basic(documents, filepath)
            
        except Exception as e:
            logger.error(f"解析 PDF 文件{filepath}失败：{str(e)}")
            raise Exception(f"PDF 解析失败：{str(e)}")
    
    def _parse_basic(self, documents: List[Document], filepath: str) -> List[Document]:
        """
        基础解析：仅过滤完全重复的页面
        :param documents: 原始文档列表
        :param filepath: 文件路径
        :return: 清理后的文档列表
        """
        cleaned_docs = []
        prev_content = ""
        for doc in documents:
            current_content = doc.page_content
            if prev_content and current_content == prev_content:
                logger.info(f"PDF {filepath} 中检测到重复页眉/页脚，已过滤")
                continue
            cleaned_docs.append(doc)
            prev_content = current_content
        
        logger.info(f"PDF 文件{filepath}基础解析成功，共{len(cleaned_docs)}页")
        return cleaned_docs
    
    def _parse_with_layout_cleaning(self, documents: List[Document], filepath: str) -> List[Document]:
        """
        增强解析：使用版式清理器处理
        :param documents: 原始文档列表
        :param filepath: 文件路径
        :return: 清理后的文档列表（合并为单个 Document）
        """
        # 提取所有页面内容
        pages = [doc.page_content for doc in documents]
        
        # 使用版式清理器进行深度清理
        cleaned_text = self.layout_cleaner.clean_multiple_pages(pages)
        
        if not cleaned_text or not cleaned_text.strip():
            logger.warning(f"PDF {filepath} 清理后无有效内容")
            return []
        
        # 创建单个 Document（后续由分块器处理）
        doc = Document(
            page_content=cleaned_text,
            metadata={
                "source": filepath,
                "total_pages": len(documents),
                "layout_cleaned": True
            }
        )
        
        logger.info(f"PDF 文件{filepath}增强解析成功，清理后文本长度: {len(cleaned_text)}")
        return [doc]
