"""
RAG 生成器
负责结合检索结果生成回答
"""
from typing import List
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from app.utils.prompt_loader import load_rag_prompts
from langchain_community.chat_models.tongyi import ChatTongyi
from app.utils.config_handler import rag_conf

# 初始化聊天模型
chat_model = ChatTongyi(model=rag_conf["chat_model_name"])
from app.utils.logger_handler import logger


class RAGGenerator:
    """RAG 生成器"""
    
    def __init__(self):
        self.prompt_text = load_rag_prompts()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.model = chat_model
        self.chain = self._init_chain()
    
    def _init_chain(self):
        """初始化生成链"""
        return self.prompt_template | self.model | StrOutputParser()
    
    def generate(self, query: str, context_docs: List[Document]) -> str:
        """
        基于检索结果生成回答
        :param query: 用户问题
        :param context_docs: 检索到的文档列表
        :return: 生成的回答
        """
        try:
            # 组装上下文
            context = self._format_context(context_docs)
            
            # 生成回答
            response = self.chain.invoke({
                "input": query,
                "context": context,
            })
            
            logger.info(f"RAG 生成完成，问题：{query[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"RAG 生成失败：{str(e)}")
            raise Exception(f"RAG 生成失败：{str(e)}")
    
    def _format_context(self, docs: List[Document]) -> str:
        """格式化检索结果为上下文字符串"""
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            context_parts.append(
                f"【参考资料{i}】：{doc.page_content} | 来源：{doc.metadata.get('source', '未知')}"
            )
        
        return "\n\n".join(context_parts)
    
    def rag_summarize(self, query: str) -> str:
        """
        完整的 RAG 流程：检索 + 生成
        :param query: 用户问题
        :return: 回答
        """
        from core.rag.retriever import RetrieverService
        
        retriever = RetrieverService()
        context_docs = retriever.retrieve(query)
        
        return self.generate(query, context_docs)
