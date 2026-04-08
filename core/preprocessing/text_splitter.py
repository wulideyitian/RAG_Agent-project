"""
文本分块服务（重点优化 - 支持格式感知分块）
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
    """文本分块服务（支持格式感知）"""
    
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
        
        # 格式专属分块器（延迟初始化）
        self._pdf_splitter = None
        self._docx_splitter = None
        self._md_splitter = None
    
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
            # 检查空文本 - 返回空列表，与其他方法保持一致
            if not text or not text.strip():
                logger.warning("分割空文本")
                return []
            
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
        # 检查空文本 - 返回空列表，与其他方法保持一致
        if not text or not text.strip():
            logger.warning("自适应分割空文本")
            return []
        
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
    
    def format_aware_split(
        self,
        documents: List[Document],
        source_format: str = "auto"
    ) -> List[Document]:
        """
        格式感知的分块策略（主入口）
        :param documents: 待分割的文档列表
        :param source_format: 来源格式 ("pdf" | "docx" | "md" | "auto")
        :return: 分割后的文档列表
        """
        if not documents:
            logger.warning("没有文档可分割")
            return []
        
        # 如果只有一个文档且已按结构分块（来自增强解析器），直接返回
        if len(documents) == 1:
            metadata = documents[0].metadata
            # 检查是否已经有标题层级信息（说明已经被结构化分块）
            if 'heading_level' in metadata or 'section_index' in metadata:
                logger.info("文档已结构化，跳过二次分块")
                return documents
        
        # 根据格式选择分块策略
        if source_format == "pdf":
            return self._split_pdf_optimized(documents)
        elif source_format == "docx":
            return self._split_docx_optimized(documents)
        elif source_format == "md":
            return self._split_md_optimized(documents)
        else:
            # 自动检测或使用默认策略
            logger.info("使用默认自适应分块策略")
            return self.split_documents(documents, strategy="recursive")
    
    def _get_pdf_splitter(self) -> RecursiveCharacterTextSplitter:
        """获取 PDF 专属分块器（懒加载）"""
        if self._pdf_splitter is None:
            # PDF 使用更小的块，避免跨页内容混杂
            pdf_chunk_size = chroma_conf.get("chunking", {}).get("pdf", {}).get("chunk_size", 80)
            pdf_chunk_overlap = chroma_conf.get("chunking", {}).get("pdf", {}).get("chunk_overlap", 15)
            
            self._pdf_splitter = RecursiveCharacterTextSplitter(
                chunk_size=pdf_chunk_size,
                chunk_overlap=pdf_chunk_overlap,
                separators=["\n\n", "\n", "。", ".", "！", "!", "？", "?"],
                length_function=len,
            )
            logger.info(f"PDF 分块器初始化: chunk_size={pdf_chunk_size}, overlap={pdf_chunk_overlap}")
        return self._pdf_splitter
    
    def _get_docx_splitter(self) -> RecursiveCharacterTextSplitter:
        """获取 Word 专属分块器（懒加载）"""
        if self._docx_splitter is None:
            # Word 可用较大的块，因为已有标题结构
            docx_chunk_size = chroma_conf.get("chunking", {}).get("docx", {}).get("chunk_size", 150)
            docx_chunk_overlap = chroma_conf.get("chunking", {}).get("docx", {}).get("chunk_overlap", 25)
            
            self._docx_splitter = RecursiveCharacterTextSplitter(
                chunk_size=docx_chunk_size,
                chunk_overlap=docx_chunk_overlap,
                separators=["\n\n", "\n", "。", ".", "；", ";"],
                length_function=len,
            )
            logger.info(f"Word 分块器初始化: chunk_size={docx_chunk_size}, overlap={docx_chunk_overlap}")
        return self._docx_splitter
    
    def _get_md_splitter(self) -> RecursiveCharacterTextSplitter:
        """获取 Markdown 专属分块器（懒加载）"""
        if self._md_splitter is None:
            # Markdown 可利用结构，使用中等块大小
            md_chunk_size = chroma_conf.get("chunking", {}).get("md", {}).get("chunk_size", 200)
            md_chunk_overlap = chroma_conf.get("chunking", {}).get("md", {}).get("chunk_overlap", 30)
            
            self._md_splitter = RecursiveCharacterTextSplitter(
                chunk_size=md_chunk_size,
                chunk_overlap=md_chunk_overlap,
                separators=["\n\n", "\n", "```", "。", "."],
                length_function=len,
            )
            logger.info(f"Markdown 分块器初始化: chunk_size={md_chunk_size}, overlap={md_chunk_overlap}")
        return self._md_splitter
    
    def _split_pdf_optimized(self, documents: List[Document]) -> List[Document]:
        """
        PDF 优化分块
        - 更小的 chunk_size（避免跨页内容混杂）
        - 优先按段落分割
        - 禁用跨页合并
        """
        splitter = self._get_pdf_splitter()
        
        # 过滤空文档
        valid_documents = [doc for doc in documents if doc.page_content and doc.page_content.strip()]
        
        if not valid_documents:
            return []
        
        chunks = splitter.split_documents(valid_documents)
        
        # 为每个 chunk 添加 PDF 特有元数据
        for chunk in chunks:
            chunk.metadata['format_optimized'] = 'pdf'
        
        logger.info(f"PDF 优化分块完成，共{len(chunks)}个文本块")
        return chunks
    
    def _split_docx_optimized(self, documents: List[Document]) -> List[Document]:
        """
        Word 优化分块
        - 利用标题层级作为天然边界
        - 相同标题级别的内容保持在一起
        - 表格单独成块
        """
        # 如果文档已经按标题分块，直接使用
        structured_docs = [doc for doc in documents if 'heading_level' in doc.metadata]
        
        if structured_docs:
            logger.info(f"Word 文档已按标题分块，共{len(structured_docs)}个结构块")
            # 对每个结构块进行细粒度分块（如果需要）
            all_chunks = []
            for doc in structured_docs:
                # 如果块太大，再进行细分
                if len(doc.page_content) > 300:
                    splitter = self._get_docx_splitter()
                    sub_chunks = splitter.split_documents([doc])
                    # 保留原始元数据
                    for chunk in sub_chunks:
                        chunk.metadata.update(doc.metadata)
                        chunk.metadata['format_optimized'] = 'docx'
                    all_chunks.extend(sub_chunks)
                else:
                    doc.metadata['format_optimized'] = 'docx'
                    all_chunks.append(doc)
            return all_chunks
        else:
            # 没有结构信息，使用标准分块
            splitter = self._get_docx_splitter()
            valid_documents = [doc for doc in documents if doc.page_content and doc.page_content.strip()]
            chunks = splitter.split_documents(valid_documents)
            
            for chunk in chunks:
                chunk.metadata['format_optimized'] = 'docx'
            
            logger.info(f"Word 标准分块完成，共{len(chunks)}个文本块")
            return chunks
    
    def _split_md_optimized(self, documents: List[Document]) -> List[Document]:
        """
        Markdown 优化分块
        - 按 ## 或 ### 标题分割
        - 代码块保持完整
        - 列表项不拆分
        """
        # 如果文档已经按标题分块，直接使用
        structured_docs = [doc for doc in documents if 'heading_level' in doc.metadata]
        
        if structured_docs:
            logger.info(f"Markdown 文档已按标题分块，共{len(structured_docs)}个结构块")
            # 对每个结构块进行细粒度分块（如果需要）
            all_chunks = []
            for doc in structured_docs:
                # 如果块太大，再进行细分（但要保持代码块完整）
                if len(doc.page_content) > 400:
                    splitter = self._get_md_splitter()
                    sub_chunks = splitter.split_documents([doc])
                    # 保留原始元数据
                    for chunk in sub_chunks:
                        chunk.metadata.update(doc.metadata)
                        chunk.metadata['format_optimized'] = 'md'
                    all_chunks.extend(sub_chunks)
                else:
                    doc.metadata['format_optimized'] = 'md'
                    all_chunks.append(doc)
            return all_chunks
        else:
            # 没有结构信息，使用标准分块
            splitter = self._get_md_splitter()
            valid_documents = [doc for doc in documents if doc.page_content and doc.page_content.strip()]
            chunks = splitter.split_documents(valid_documents)
            
            for chunk in chunks:
                chunk.metadata['format_optimized'] = 'md'
            
            logger.info(f"Markdown 标准分块完成，共{len(chunks)}个文本块")
            return chunks
