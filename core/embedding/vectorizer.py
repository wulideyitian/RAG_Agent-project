"""
向量化处理器
负责文本到向量的转换流程
"""
from typing import List
from langchain_core.documents import Document
from app.utils.logger_handler import logger
from core.embedding.embed_model import EmbedModelService


class Vectorizer:
    """向量化处理器"""
    
    def __init__(self):
        self.embed_service = EmbedModelService()
    
    def vectorize_documents(self, documents: List[Document]) -> tuple:
        """
        向量化文档
        :param documents: Document 列表
        :return: (texts, embeddings, metadatas)
        """
        try:
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # 批量向量化
            embeddings = self.embed_service.embed_documents(texts)
            
            logger.info(f"成功向量化{len(texts)}个文档")
            return texts, embeddings, metadatas
            
        except Exception as e:
            logger.error(f"向量化失败：{str(e)}")
            raise Exception(f"向量化失败：{str(e)}")
    
    def vectorize_query(self, query: str) -> List[float]:
        """
        向量化查询
        :param query: 查询文本
        :return: 查询向量
        """
        try:
            embedding = self.embed_service.embed_query(query)
            logger.debug(f"查询已向量化，维度：{len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"查询向量化失败：{str(e)}")
            raise Exception(f"查询向量化失败：{str(e)}")
