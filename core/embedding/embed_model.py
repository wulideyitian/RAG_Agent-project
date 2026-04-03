"""
嵌入模型服务
管理嵌入模型的加载和使用
"""
from abc import ABC, abstractmethod
from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import DashScopeEmbeddings
from app.utils.config_handler import rag_conf


class EmbedModelService:
    """嵌入模型服务"""
    
    def __init__(self):
        self.model_name = rag_conf.get("embedding_model_name", "text-embedding-v2")
        self._model = None
    
    @property
    def model(self) -> Embeddings:
        """懒加载嵌入模型"""
        if self._model is None:
            self._model = self._load_model()
        return self._model
    
    def _load_model(self) -> Embeddings:
        """加载嵌入模型"""
        try:
            return DashScopeEmbeddings(model=self.model_name)
        except Exception as e:
            raise RuntimeError(f"加载嵌入模型失败：{str(e)}")
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        将文档列表转换为向量
        :param texts: 文本列表
        :return: 向量列表
        """
        return self.model.embed_documents(texts)
    
    def embed_query(self, text: str) -> list[float]:
        """
        将查询文本转换为向量
        :param text: 查询文本
        :return: 向量
        """
        return self.model.embed_query(text)
