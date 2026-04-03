"""
分块质量检查器
评估和优化文本分块的质量
"""
import re
from typing import List, Dict
from langchain_core.documents import Document
from app.utils.logger_handler import logger


class QualityChecker:
    """分块质量检查器"""
    
    def __init__(self):
        self.min_chunk_length = 50  # 最小块长度
        self.max_chunk_length = 2000  # 最大块长度
        self.similarity_threshold = 0.8  # 相似度阈值修正为标准值
        # 有效字符比例阈值
        self.valid_char_ratio_threshold = 0.5  # 兼容所有正常文本
    
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
        stripped = content.strip()
        
        # 空文本直接返回 False
        if not stripped:
            return False
        
        # 统一有效字符正则：支持中文、英文、数字、常用标点
        # \u4e00-\u9fff: 中文汉字
        # \u3000-\u303f: 中文标点符号
        # \uff00-\uffef: 全角字符（包括英文、数字、标点）
        # a-zA-Z0-9: 英文字母和数字
        # \s: 空白字符
        valid_pattern = re.compile(
            r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffefa-zA-Z0-9\s]'
        )
        valid_chars = len(valid_pattern.findall(stripped))
        total_chars = len(stripped)
        
        if total_chars == 0:
            return False
        
        ratio = valid_chars / total_chars
        if ratio < self.valid_char_ratio_threshold:
            return False
        
        # 优化完整句子判断：避免标点文本被误判
        # 中文标点：.!.,;:?!
        # 英文标点：.,;:!?"'
        has_sentence = bool(re.search(r'[.!.,;:?!"\']{1,}', stripped))
        has_meaningful_content = len(stripped.split()) >= 3  # 至少 3 个单词/中文字符
        
        # 长文本且有实际内容，即使没有标点也接受
        if len(stripped) >= self.min_chunk_length and has_meaningful_content:
            return True
        
        # 必须满足：有句子结构 或 有实际意义内容
        if not (has_sentence or has_meaningful_content):
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
        
        # 修复空文本重复判断逻辑：任一为空则不视为重复
        if not content1 or not content2:
            return False
        
        # 完全相同的情况
        if content1 == content2:
            return True
        
        # 计算相似度（基于字符级别）
        min_len = min(len(content1), len(content2))
        if min_len == 0:
            return False
        
        compare_len = min(min_len, 100)  # 只比较前 100 字符
        similarity = sum(
            c1 == c2 
            for c1, c2 in zip(content1[:compare_len], content2[:compare_len])
        ) / compare_len
        
        # 使用标准相似度阈值 0.8
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
