"""
分块质量检查器
评估和优化文本分块的质量
"""
from typing import List, Dict
from langchain_core.documents import Document
from app.utils.logger_handler import logger


class QualityChecker:
    """分块质量检查器"""
    
    def __init__(self):
        self.min_chunk_length = 50  # 最小块长度
        self.max_chunk_length = 2000  # 最大块长度
        self.similarity_threshold = 0.9  # 相似度阈值
    
    def check_chunks(self, chunks: List[Document]) -> List[Document]:
        """
        检查并过滤低质量分块
        :param chunks: 分块列表
        :return: 过滤后的分块列表
        """
        valid_chunks = []
        
        for i, chunk in enumerate(chunks):
            content = chunk.page_content
            
            # 检查 1: 长度检查
            if not self._check_length(content):
                logger.debug(f"分块{i}长度不合格，已过滤")
                continue
            
            # 检查 2: 内容质量检查
            if not self._check_content_quality(content):
                logger.debug(f"分块{i}内容质量不合格，已过滤")
                continue
            
            # 检查 3: 重复度检查（与前一个分块比较）
            if i > 0 and self._is_duplicate(chunk, chunks[i-1]):
                logger.debug(f"分块{i}与前一重复，已过滤")
                continue
            
            valid_chunks.append(chunk)
        
        logger.info(f"质量检查完成，{len(valid_chunks)}/{len(chunks)}个分块通过")
        return valid_chunks
    
    def _check_length(self, content: str) -> bool:
        """检查长度是否合格"""
        stripped = content.strip()
        if len(stripped) < self.min_chunk_length:
            return False
        if len(stripped) > self.max_chunk_length:
            return False
        return True
    
    def _check_content_quality(self, content: str) -> bool:
        """检查内容质量"""
        # 计算有效字符比例
        valid_chars = sum(1 for c in content if c.isalnum() or c.isspace())
        total_chars = len(content)
        
        if total_chars == 0:
            return False
        
        ratio = valid_chars / total_chars
        if ratio < 0.6:
            return False
        
        # 检查是否有实际语义内容（至少有一个完整句子）
        has_sentence = any(punct in content for punct in '.!.!??.!,,;:')
        if not has_sentence:
            return False
        
        return True
    
    def _is_duplicate(self, chunk1: Document, chunk2: Document) -> bool:
        """
        检查两个分块是否重复
        :param chunk1: 分块 1
        :param chunk2: 分块 2
        :return: True 如果重复
        """
        content1 = chunk1.page_content.strip()
        content2 = chunk2.page_content.strip()
        
        # 简单的前缀比较（可以优化为更复杂的相似度算法）
        min_len = min(len(content1), len(content2))
        if min_len == 0:
            return False
        
        compare_len = min(min_len, 100)  # 只比较前 100 字符
        similarity = sum(
            c1 == c2 
            for c1, c2 in zip(content1[:compare_len], content2[:compare_len])
        ) / compare_len
        
        return similarity > self.similarity_threshold
    
    def optimize_chunks(self, chunks: List[Document]) -> List[Document]:
        """
        优化分块（合并过小的块，拆分过大的块）
        :param chunks: 原始分块
        :return: 优化后的分块
        """
        if not chunks:
            return []
        
        optimized = []
        buffer = ""
        buffer_metadata = {}
        
        for chunk in chunks:
            content = chunk.page_content
            
            # 如果当前块太小，尝试与后续块合并
            if len(content) < self.min_chunk_length:
                buffer += "\n\n" + content if buffer else content
                buffer_metadata.update(chunk.metadata)
                continue
            
            # 如果缓冲区有内容，先处理
            if buffer:
                merged_content = buffer + "\n\n" + content
                if len(merged_content) <= self.max_chunk_length:
                    # 合并后不超过最大值，则合并
                    optimized.append(Document(
                        page_content=merged_content,
                        metadata=buffer_metadata
                    ))
                    buffer = ""
                    buffer_metadata = {}
                else:
                    # 否则单独添加缓冲区内容
                    optimized.append(Document(
                        page_content=buffer,
                        metadata=buffer_metadata
                    ))
                    buffer = content
                    buffer_metadata = chunk.metadata.copy()
            else:
                optimized.append(chunk)
        
        # 处理剩余的缓冲区内容
        if buffer:
            optimized.append(Document(
                page_content=buffer,
                metadata=buffer_metadata
            ))
        
        logger.info(f"分块优化完成，{len(optimized)}/{len(chunks)}个分块")
        return optimized
