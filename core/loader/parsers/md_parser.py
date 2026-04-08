"""
Markdown 文件解析器（增强版 - 支持层级分块）
"""
from typing import List, Dict
from langchain_core.documents import Document
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from app.utils.logger_handler import logger
from core.preprocessing.text_cleaner import TextCleaner
import re


class MarkdownParser:
    """Markdown 文件解析器（增强版 - 支持层级分块）"""
    
    def __init__(self, enable_hierarchical_splitting: bool = True, min_heading_level: int = 2):
        """
        :param enable_hierarchical_splitting: 是否启用层级分块
        :param min_heading_level: 最小分块标题级别 (2 表示从 ## 开始分块)
        """
        self.text_cleaner = TextCleaner()
        self.enable_hierarchical_splitting = enable_hierarchical_splitting
        self.min_heading_level = min_heading_level
        if enable_hierarchical_splitting:
            logger.info(f"Markdown 层级分块已启用 (最小标题级别: {min_heading_level})")
    
    def parse(self, filepath: str) -> List[Document]:
        """
        解析 Markdown 文件
        :param filepath: 文件路径
        :return: Document 列表
        """
        try:
            # 如果启用了层级分块，使用增强解析
            if self.enable_hierarchical_splitting:
                return self._parse_with_hierarchy(filepath)
            else:
                # 否则使用基础解析
                return self._parse_basic(filepath)
            
        except Exception as e:
            logger.error(f"解析 Markdown 文件{filepath}失败：{str(e)}")
            raise Exception(f"Markdown 解析失败：{str(e)}")
    
    def _parse_basic(self, filepath: str) -> List[Document]:
        """
        基础解析：使用 UnstructuredMarkdownLoader
        :param filepath: 文件路径
        :return: Document 列表
        """
        loader = UnstructuredMarkdownLoader(filepath)
        documents = loader.load()
        
        if not documents:
            return []
        
        # 清理文本
        cleaned_content = self.text_cleaner.clean(
            documents[0].page_content, 
            'md'
        )
        
        doc = Document(
            page_content=cleaned_content, 
            metadata={"source": filepath}
        )
        
        logger.info(f"Markdown 文件{filepath}基础解析成功")
        return [doc]
    
    def _parse_with_hierarchy(self, filepath: str) -> List[Document]:
        """
        增强解析：基于标题层级分块
        :param filepath: 文件路径
        :return: Document 列表（按标题分块）
        """
        # 读取原始 Markdown 内容
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content or not content.strip():
            logger.warning(f"Markdown 文件{filepath}为空")
            return []
        
        # 按标题分割内容
        structured_chunks = self._split_by_headings(content)
        
        if not structured_chunks:
            logger.warning(f"Markdown 文件{filepath}未提取到结构化内容")
            return []
        
        # 转换为 Document 列表
        documents = []
        for chunk in structured_chunks:
            # 清理文本
            cleaned_content = self.text_cleaner.clean(chunk['content'], 'md')
            
            if not cleaned_content or not cleaned_content.strip():
                continue
            
            doc = Document(
                page_content=cleaned_content,
                metadata={
                    "source": filepath,
                    "heading_level": chunk.get('heading_level', 0),
                    "heading_text": chunk.get('heading_text', ''),
                    "parent_heading": chunk.get('parent_heading', ''),
                    "section_index": chunk.get('section_index', 0),
                }
            )
            documents.append(doc)
        
        logger.info(f"Markdown 文件{filepath}增强解析成功，共{len(documents)}个结构块")
        return documents
    
    def _split_by_headings(self, content: str) -> List[Dict]:
        """
        按标题分割 Markdown 内容
        :param content: Markdown 原始内容
        :return: 结构化块列表
        """
        lines = content.split('\n')
        chunks = []
        current_heading_level = 0
        current_heading_text = ""
        parent_heading = ""
        current_content = []
        section_index = 0
        
        # 用于追踪父级标题
        heading_stack = []  # [(level, text), ...]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 检测标题行
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                
                # 只有达到最小分块级别时才创建新块
                if level >= self.min_heading_level:
                    # 保存之前的块
                    if current_content:
                        chunks.append({
                            'heading_level': current_heading_level,
                            'heading_text': current_heading_text,
                            'parent_heading': parent_heading,
                            'content': '\n'.join(current_content),
                            'section_index': section_index
                        })
                        section_index += 1
                    
                    # 更新父级标题
                    parent_heading = self._get_parent_heading(heading_stack, level)
                    
                    # 更新标题栈
                    self._update_heading_stack(heading_stack, level, heading_text)
                    
                    # 开始新块
                    current_heading_level = level
                    current_heading_text = heading_text
                    current_content = []
                else:
                    # 低于最小分块级别的标题作为内容的一部分
                    current_content.append(line)
            else:
                # 普通内容行
                current_content.append(line)
            
            i += 1
        
        # 保存最后一个块
        if current_content:
            chunks.append({
                'heading_level': current_heading_level,
                'heading_text': current_heading_text,
                'parent_heading': parent_heading,
                'content': '\n'.join(current_content),
                'section_index': section_index
            })
        
        logger.debug(f"Markdown 分割为 {len(chunks)} 个块")
        return chunks
    
    def _get_parent_heading(self, heading_stack: List[tuple], current_level: int) -> str:
        """
        获取当前标题的父级标题
        :param heading_stack: 标题栈
        :param current_level: 当前标题级别
        :return: 父级标题文本
        """
        # 找到比当前级别低的最近标题
        for level, text in reversed(heading_stack):
            if level < current_level:
                return text
        return ""
    
    def _update_heading_stack(self, heading_stack: List[tuple], level: int, text: str):
        """
        更新标题栈
        :param heading_stack: 标题栈
        :param level: 新标题级别
        :param text: 新标题文本
        """
        # 移除所有级别大于等于当前级别的标题
        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        
        # 添加新标题
        heading_stack.append((level, text))
