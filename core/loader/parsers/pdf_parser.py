"""
PDF 文件解析器
"""
import re
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from app.utils.logger_handler import logger


class PDFParser:
    """PDF 文件解析器"""
    
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
            
            # 过滤重复页眉页脚
            cleaned_docs = []
            prev_content = ""
            for doc in documents:
                current_content = doc.page_content
                if prev_content and current_content == prev_content:
                    logger.info(f"PDF{filepath}中检测到重复页眉/页脚，已过滤")
                    continue
                cleaned_docs.append(doc)
                prev_content = current_content
            
            logger.info(f"PDF 文件{filepath}解析成功，共{len(cleaned_docs)}页")
            return cleaned_docs
            
        except Exception as e:
            logger.error(f"解析 PDF 文件{filepath}失败：{str(e)}")
            raise Exception(f"PDF 解析失败：{str(e)}")
