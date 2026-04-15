"""
Reranker 服务
负责使用 BGE-reranker-base 模型对检索结果进行重排序
"""
import asyncio
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor
from langchain_core.documents import Document
from app.utils.logger_handler import logger


class RerankerService:
    """重排序服务 - 使用 BGE-reranker-base 模型"""
    
    _instance = None
    _model = None
    _executor = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化重排序服务"""
        if hasattr(self, '_initialized'):
            return
        
        from app.utils.config_handler import rerank_conf
        
        self.enabled = rerank_conf.get("enabled", True)
        self.model_name = rerank_conf.get("model_name", "BAAI/bge-reranker-base")
        self.top_n = rerank_conf.get("top_n", 3)
        self.batch_size = rerank_conf.get("batch_size", 32)
        self.device = rerank_conf.get("device", "auto")
        self.timeout = rerank_conf.get("timeout", 30)  # 超时时间（秒）
        
        self._initialized = True
        self._thread_pool = ThreadPoolExecutor(max_workers=2)
        
        if self.enabled:
            logger.info(f"Reranker 服务初始化，模型：{self.model_name}")
        else:
            logger.info("Reranker 服务已禁用")
    
    def _load_model(self):
        """懒加载重排序模型"""
        if self._model is not None:
            return self._model
        
        try:
            from FlagEmbedding import FlagReranker
            
            logger.info(f"正在加载 Reranker 模型：{self.model_name}...")
            
            # 确定设备
            device = self.device
            if device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            
            self._model = FlagReranker(
                self.model_name,
                use_fp16=True if device == "cuda" else False,
                device=device
            )
            
            logger.info(f"Reranker 模型加载成功，设备：{device}")
            return self._model
            
        except ImportError:
            logger.error("FlagEmbedding 未安装，请运行：pip install FlagEmbedding")
            raise
        except Exception as e:
            logger.error(f"Reranker 模型加载失败：{str(e)}", exc_info=True)
            raise
    
    async def rerank(
        self, 
        query: str, 
        documents: List[Document]
    ) -> List[Document]:
        """
        异步重排序文档
        
        :param query: 查询文本
        :param documents: 待重排序的文档列表
        :return: 重排序后的文档列表（按相关性降序）
        """
        if not self.enabled:
            logger.debug("Reranker 已禁用，返回原始文档")
            return documents[:self.top_n]
        
        if not documents:
            return []
        
        try:
            # 在线程池中执行同步的重排序操作
            loop = asyncio.get_event_loop()
            ranked_docs = await asyncio.wait_for(
                loop.run_in_executor(
                    self._thread_pool,
                    self._rerank_sync,
                    query,
                    documents
                ),
                timeout=self.timeout
            )
            
            logger.debug(f"重排序完成，从 {len(documents)} 个文档中选出 top-{len(ranked_docs)}")
            return ranked_docs
            
        except asyncio.TimeoutError:
            logger.warning(f"重排序超时（{self.timeout}s），返回原始文档")
            return documents[:self.top_n]
        except Exception as e:
            logger.error(f"重排序失败：{str(e)}，返回原始文档", exc_info=True)
            # 降级：返回原始文档的前 top_n 个
            return documents[:self.top_n]
    
    def _rerank_sync(
        self, 
        query: str, 
        documents: List[Document]
    ) -> List[Document]:
        """
        同步重排序（在线程池中执行）
        
        :param query: 查询文本
        :param documents: 待重排序的文档列表
        :return: 重排序后的文档列表
        """
        try:
            # 加载模型
            model = self._load_model()
            
            # 准备输入
            pairs = [[query, doc.page_content] for doc in documents]
            
            # 批量计算分数
            scores = model.compute_score(pairs, batch_size=self.batch_size)
            
            # 如果只有一个文档，scores 是标量，需要转换为列表
            if isinstance(scores, (int, float)):
                scores = [scores]
            
            # 将分数与文档配对
            scored_docs = list(zip(documents, scores))
            
            # 按分数降序排序
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # 添加分数到元数据
            ranked_docs = []
            for doc, score in scored_docs[:self.top_n]:
                # 复制文档并添加分数
                new_doc = Document(
                    page_content=doc.page_content,
                    metadata={**doc.metadata, "rerank_score": float(score)}
                )
                ranked_docs.append(new_doc)
            
            return ranked_docs
            
        except Exception as e:
            logger.error(f"同步重排序失败：{str(e)}", exc_info=True)
            raise
    
    def compute_scores(
        self, 
        query: str, 
        documents: List[Document]
    ) -> List[Tuple[Document, float]]:
        """
        计算文档相关性分数（同步方法，用于调试）
        
        :param query: 查询文本
        :param documents: 文档列表
        :return: (文档, 分数) 元组列表
        """
        try:
            model = self._load_model()
            pairs = [[query, doc.page_content] for doc in documents]
            scores = model.compute_score(pairs, batch_size=self.batch_size)
            
            if isinstance(scores, (int, float)):
                scores = [scores]
            
            return list(zip(documents, scores))
            
        except Exception as e:
            logger.error(f"计算分数失败：{str(e)}", exc_info=True)
            raise
    
    def shutdown(self):
        """关闭线程池"""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
            logger.info("Reranker 服务已关闭")
