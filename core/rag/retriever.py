"""
检索服务
负责从向量库中检索相关文档
"""
from typing import List
from langchain_core.documents import Document
from app.utils.logger_handler import logger
from core.rag.vector_store import VectorStoreService


class RetrieverService:
    """检索服务"""
    
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
    
    def retrieve(self, query: str, k: int = None) -> List[Document]:
        """
        检索相关文档
        :param query: 查询文本
        :param k: 返回文档数量（可选）
        :return: 相关文档列表
        """
        try:
            if k:
                # 创建新的检索器实例，避免修改共享状态
                from app.utils.config_handler import chroma_conf
                custom_retriever = self.vector_store.vector_store.as_retriever(
                    search_kwargs={"k": k}
                )
                docs = custom_retriever.invoke(query)
            else:
                docs = self.retriever.invoke(query)
            
            logger.debug(f"检索到{len(docs)}篇相关文档")
            return docs
            
        except Exception as e:
            logger.error(f"检索失败：{str(e)}")
            raise Exception(f"检索失败：{str(e)}")
    
    def retrieve_with_scores(self, query: str) -> List[tuple]:
        """
        检索带相似度分数的文档
        :param query: 查询文本
        :return: (Document, score) 元组列表
        """
        try:
            results = self.vector_store.vector_store.similarity_search_with_score(query, k=3)
            logger.debug(f"检索到{len(results)}篇带分数文档")
            return results
            
        except Exception as e:
            logger.error(f"带分数检索失败：{str(e)}")
            raise Exception(f"带分数检索失败：{str(e)}")
