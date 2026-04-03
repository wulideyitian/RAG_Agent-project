"""
文本分块服务（重点优化）
提供多种分块策略
"""
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
        # 默认配置
        self.chunk_size = chroma_conf.get("chunk_size", 500)
        self.chunk_overlap = chroma_conf.get("chunk_overlap", 50)
        self.separators = chroma_conf.get("separators", ["\n\n", "\n", "。", ".", "!", "！", "?", "？", " ", ""])
        
        # 初始化分块器
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
            if strategy == "recursive":
                chunks = self.recursive_splitter.split_documents(documents)
            elif strategy == "character":
                chunks = self.character_splitter.split_documents(documents)
            else:
                logger.warning(f"未知的分块策略：{strategy}，使用默认 recursive")
                chunks = self.recursive_splitter.split_documents(documents)
            
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
            temp_doc = Document(page_content=text, metadata=metadata or {})
            return self.split_documents([temp_doc], strategy)
            
        except Exception as e:
            logger.error(f"文本分割失败：{str(e)}")
            raise Exception(f"文本分块失败：{str(e)}")
    
    def adaptive_split(
        self, 
        text: str, 
        source: str = "",
        min_chunk_size: int = 100,
        max_chunk_size: int = 1000
    ) -> List[Document]:
        """
        自适应分块（根据文本特征自动选择策略）
        :param text: 待分割的文本
        :param source: 来源标识
        :param min_chunk_size: 最小块大小
        :param max_chunk_size: 最大块大小
        :return: Document 列表
        """
        # 检测文本特征
        has_sections = "\n\n" in text
        has_sentences = any(c in text for c in ".!.!??.!")
        
        # 动态调整分块策略
        if has_sections and len(text) > max_chunk_size:
            # 有明确章节结构的长文本，使用较大的 chunk_size
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=max_chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n"],
            )
        elif has_sentences:
            # 有句子结构的文本，使用标准配置
            splitter = self.recursive_splitter
        else:
            # 无结构文本，使用较小的 chunk_size
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=min_chunk_size,
                chunk_overlap=min_chunk_size // 2,
                separators=[""],
            )
        
        try:
            temp_doc = Document(page_content=text, metadata={"source": source})
            chunks = splitter.split_documents([temp_doc])
            
            logger.info(f"自适应分块完成，共{len(chunks)}个文本块")
            return chunks
            
        except Exception as e:
            logger.error(f"自适应分块失败：{str(e)}")
            raise Exception(f"自适应分块失败：{str(e)}")
