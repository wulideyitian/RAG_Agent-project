"""
检索服务
负责从向量库中检索相关文档
"""
from typing import List
from langchain_core.documents import Document
from app.utils.logger_handler import logger
from core.rag.vector_store import VectorStoreService
from core.rerank.reranker import RerankerService


class RetrieverService:
    """检索服务"""
    
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.reranker = RerankerService()
        
        # 从配置中获取初始召回数量
        from app.utils.config_handler import rerank_conf
        self.initial_k = rerank_conf.get("initial_k", 10)
    
    async def retrieve(self, query: str, k: int = None) -> List[Document]:
        """
        检索相关文档（带重排序）
        :param query: 查询文本
        :param k: 返回文档数量（可选，默认使用 rerank.yml 中的 top_n）
        :return: 相关文档列表（已重排序）
        """
        try:
            # 确定初始召回数量
            initial_k = k if k else self.initial_k
            
            # 第一步：向量检索（召回更多候选文档）
            custom_retriever = self.vector_store.vector_store.as_retriever(
                search_kwargs={"k": initial_k}
            )
            docs = custom_retriever.invoke(query)
            
            logger.debug(f"向量检索到 {len(docs)} 篇候选文档")
            
            # 第二步：重排序（如果启用）
            if docs:
                ranked_docs = await self.reranker.rerank(query, docs)
                logger.info(f"重排序后返回 {len(ranked_docs)} 篇文档")
                return ranked_docs
            
            return []
            
        except Exception as e:
            logger.error(f"检索失败：{str(e)}")
            raise Exception(f"检索失败：{str(e)}")
    
    async def retrieve_with_scores(self, query: str) -> List[tuple]:
        """
        检索带相似度分数的文档（带重排序）
        :param query: 查询文本
        :return: (Document, score) 元组列表
        """
        try:
            # 第一步：向量检索
            results = self.vector_store.vector_store.similarity_search_with_score(
                query, k=self.initial_k
            )
            
            # 转换为 Document 列表
            docs = [doc for doc, score in results]
            
            # 第二步：重排序
            if docs:
                ranked_docs = await self.reranker.rerank(query, docs)
                # 添加 rerank 分数
                result_with_scores = [
                    (doc, doc.metadata.get("rerank_score", 0.0))
                    for doc in ranked_docs
                ]
                logger.debug(f"带分数检索到 {len(result_with_scores)} 篇文档")
                return result_with_scores
            
            return []
            
        except Exception as e:
            logger.error(f"带分数检索失败：{str(e)}")
            raise Exception(f"带分数检索失败：{str(e)}")
