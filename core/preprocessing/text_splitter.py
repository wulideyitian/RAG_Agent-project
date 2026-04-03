"""
文本分块服务（重点优化）
提供多种分块策略
"""
import re
from typing import List, Optional
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    SentenceTransformersTokenTextSplitter,
)
from app.utils.config_handler import chroma_conf
from app.utils.logger_handler import logger


class TextSplitterService:
    """文本分块服务"""
    
    def __init__(self):
        # 默认配置 - 调小 chunk_size 确保中文长文本被分割
        self.chunk_size = chroma_conf.get("chunk_size", 100)  # 从 500 降低到 100
        self.chunk_overlap = chroma_conf.get("chunk_overlap", 20)  # 从 50 降低到 20
        # 新增中文专属分隔符优先级，符合中文语法
        # 优先级：段落 > 句子 > 短语 > 字符
        self.separators = [
            "\n\n",      # 段落分隔（最高优先级）
            "\n",        # 换行
            "。",        # 中文句号
            "！",        # 中文感叹号
            "？",        # 中文问号
            ".",         # 英文句号
            "!",         # 英文感叹号
            "?",         # 英文问号
            "；",        # 中文分号
            ";",         # 英文分号
            "，",        # 中文逗号
            ",",         # 英文逗号
            " ",         # 空格
            "",          # 字符级别（最低优先级）
        ]
        
        # 初始化分块器（使用优化后的中文分隔符）
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
        )
        
        self.character_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
    
    def split_documents(
        self, 
        documents: List[Document], 
        strategy: str = "recursive"
    ) -> List[Document]:
        """
        分割文档
        :param documents: 待分割的文档列表
        :param strategy: 分块策略 ("recursive" | "character")
        :return: 分割后的文档列表
        """
        try:
            # 过滤空文档
            valid_documents = [doc for doc in documents if doc.page_content and doc.page_content.strip()]
            
            if not valid_documents:
                logger.warning("没有有效内容可分割")
                return []
            
            if strategy == "recursive":
                chunks = self.recursive_splitter.split_documents(valid_documents)
            elif strategy == "character":
                chunks = self.character_splitter.split_documents(valid_documents)
            else:
                logger.warning(f"未知的分块策略：{strategy}，使用默认 recursive")
                chunks = self.recursive_splitter.split_documents(valid_documents)
            
            logger.info(f"文档分割完成，共{len(chunks)}个文本块")
            return chunks
            
        except Exception as e:
            logger.error(f"文档分割失败：{str(e)}")
            raise Exception(f"文本分块失败：{str(e)}")
    
    def split_text(
        self, 
        text: str, 
        strategy: str = "recursive",
        metadata: Optional[dict] = None
    ) -> List[Document]:
        """
        分割纯文本
        :param text: 待分割的文本
        :param strategy: 分块策略
        :param metadata: 元数据
        :return: Document 列表
        """
        try:
            # 检查空文本 - 返回包含空内容的 Document
            if not text or not text.strip():
                logger.warning("分割空文本")
                return [Document(page_content="", metadata=metadata or {})]
            
            temp_doc = Document(page_content=text, metadata=metadata or {})
            return self.split_documents([temp_doc], strategy)
            
        except Exception as e:
            logger.error(f"文本分割失败：{str(e)}")
            raise Exception(f"文本分块失败：{str(e)}")
    
    def adaptive_split(
        self, 
        text: str, 
        source: str = "",
        min_chunk_size: int = 50,   # 从 100 降低到 50
        max_chunk_size: int = 500   # 从 1000 降低到 500
    ) -> List[Document]:
        """
        自适应分块（根据文本特征自动选择策略）
        :param text: 待分割的文本
        :param source: 来源标识
        :param min_chunk_size: 最小块大小
        :param max_chunk_size: 最大块大小
        :return: Document 列表
        """
        # 检查空文本 - 返回空 Document
        if not text or not text.strip():
            logger.warning("自适应分割空文本")
            return [Document(page_content="", metadata={"source": source})]
        
        # 检测文本特征
        has_sections = "\n\n" in text
        # 优化句子判断：包含中英文标点
        has_sentences = bool(re.search(r'[.!.,;:?!.!?,;:"\']{1,}', text))
        
        # 动态调整分块策略
        if has_sections and len(text) > max_chunk_size:
            # 有明确章节结构的长文本，使用较大的 chunk_size
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=max_chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n"],
            )
        elif has_sentences:
            # 有句子结构的文本，使用标准配置（优化的中文分隔符）
            splitter = self.recursive_splitter
        else:
            # 无结构文本，使用较小的 chunk_size
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=min_chunk_size,
                chunk_overlap=min_chunk_size // 2,
                separators=self.separators,  # 使用优化的中文分隔符
            )
        
        try:
            temp_doc = Document(page_content=text, metadata={"source": source})
            chunks = splitter.split_documents([temp_doc])
            
            logger.info(f"自适应分块完成，共{len(chunks)}个文本块")
            return chunks
            
        except Exception as e:
            logger.error(f"自适应分块失败：{str(e)}")
            raise Exception(f"自适应分块失败：{str(e)}")
