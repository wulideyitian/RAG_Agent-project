"""
多格式文档分块适配测试
测试 PDF、Word、Markdown 的解析和分块效果
"""
import pytest
from pathlib import Path
from core.loader.parsers.pdf_parser import PDFParser
from core.loader.parsers.docx_parser import DOCXParser
from core.loader.parsers.md_parser import MarkdownParser
from core.preprocessing.text_splitter import TextSplitterService
from core.preprocessing.pdf_layout_cleaner import PDFLayoutCleaner


class TestPDFLayoutCleaner:
    """测试 PDF 版式清理器"""
    
    def setup_method(self):
        self.cleaner = PDFLayoutCleaner()
    
    def test_remove_page_numbers(self):
        """测试移除页码"""
        text = """第一章 概述
        
这是正文内容。

第 1 页

继续正文。

Page 2 of 10

更多内容。"""
        
        cleaned = self.cleaner._remove_page_numbers(text)
        
        # 应该移除页码行
        assert "第 1 页" not in cleaned
        assert "Page 2 of 10" not in cleaned
        # 应该保留正文
        assert "这是正文内容" in cleaned
        assert "继续正文" in cleaned
    
    def test_merge_broken_lines(self):
        """测试合并断行（使用正则表达式）"""
        text = """这是一个很长的句子，
被意外断行了，
需要合并在一起。

这是一个完整的段落。"""
        
        merged = self.cleaner.merge_broken_lines(text)
        
        # 前两句应该合并（逗号后面的换行被替换为空格）
        assert "这是一个很长的句子， 被意外断行了， 需要合并在一起。" in merged
        # 完整段落应该保持
        assert "这是一个完整的段落。" in merged
    
    def test_compress_blank_lines(self):
        """测试压缩空行"""
        text = """第一段。



第二段。




第三段。"""
        
        compressed = self.cleaner._compress_blank_lines(text)
        
        # 最多两个连续换行
        assert "\n\n\n" not in compressed
        assert "第一段。\n\n第二段。\n\n第三段。" == compressed
    
    def test_clean_layout_artifacts(self):
        """测试完整的版式清理流程"""
        text = """标题
        
这是一些正文内容，
被断行了。

第 1 页

更多正文。"""
        
        cleaned = self.cleaner.clean_layout_artifacts(text)
        
        # 页码应该被移除
        assert "第 1 页" not in cleaned
        # 断行应该被合并（同一句子内的换行）
        assert "这是一些正文内容， 被断行了。" in cleaned
        # 段落间的双换行应该保留（不会被合并）
        assert "被断行了。\n\n更多正文。" in cleaned
    
    def test_detect_and_remove_headers_footers(self):
        """测试检测并移除重复页眉页脚"""
        pages = [
            "页眉内容\n第一页正文\n页脚内容",
            "页眉内容\n第二页正文\n页脚内容",
            "页眉内容\n第三页正文\n页脚内容",
        ]
        
        cleaned_pages = self.cleaner.detect_and_remove_headers_footers(pages)
        
        # 页眉页脚应该被移除或减少
        header_count = sum(1 for page in cleaned_pages if "页眉内容" in page)
        footer_count = sum(1 for page in cleaned_pages if "页脚内容" in page)
        
        # 至少应该减少重复
        assert header_count < 3 or footer_count < 3


class TestPDFParser:
    """测试 PDF 解析器（增强版）"""
    
    def test_pdf_parser_initialization(self):
        """测试 PDF 解析器初始化"""
        parser = PDFParser(enable_layout_cleaning=True)
        assert parser.enable_layout_cleaning is True
        assert hasattr(parser, 'layout_cleaner')
        
        parser_basic = PDFParser(enable_layout_cleaning=False)
        assert parser_basic.enable_layout_cleaning is False
    
    @pytest.mark.skip(reason="需要实际的 PDF 文件")
    def test_parse_pdf_with_cleaning(self):
        """测试解析 PDF 并启用版式清理"""
        pdf_path = Path("data/惠普笔记本使用指南.pdf")
        if not pdf_path.exists():
            pytest.skip("PDF 文件不存在")
        
        parser = PDFParser(enable_layout_cleaning=True)
        documents = parser.parse(str(pdf_path))
        
        assert len(documents) > 0
        # 启用版式清理后，应该返回单个合并的 Document
        assert len(documents) == 1
        assert documents[0].metadata.get('layout_cleaned') is True


class TestDOCXParser:
    """测试 Word 解析器（增强版）"""
    
    def test_docx_parser_initialization(self):
        """测试 Word 解析器初始化"""
        parser = DOCXParser(enable_structure_extraction=True)
        assert parser.enable_structure_extraction is True
        
        parser_basic = DOCXParser(enable_structure_extraction=False)
        assert parser_basic.enable_structure_extraction is False
    
    @pytest.mark.skip(reason="需要实际的 Word 文件")
    def test_parse_docx_with_structure(self):
        """测试解析 Word 并提取标题结构"""
        # 创建一个测试用的 Word 文件或使用现有文件
        docx_path = Path("data/test_document.docx")
        if not docx_path.exists():
            pytest.skip("Word 文件不存在")
        
        parser = DOCXParser(enable_structure_extraction=True)
        documents = parser.parse(str(docx_path))
        
        assert len(documents) > 0
        # 检查是否包含标题层级信息
        has_heading_info = any('heading_level' in doc.metadata for doc in documents)
        assert has_heading_info is True


class TestMarkdownParser:
    """测试 Markdown 解析器（增强版）"""
    
    def test_md_parser_initialization(self):
        """测试 Markdown 解析器初始化"""
        parser = MarkdownParser(enable_hierarchical_splitting=True)
        assert parser.enable_hierarchical_splitting is True
        assert parser.min_heading_level == 2
        
        parser_basic = MarkdownParser(enable_hierarchical_splitting=False)
        assert parser_basic.enable_hierarchical_splitting is False
    
    def test_split_by_headings(self):
        """测试按标题分割 Markdown"""
        parser = MarkdownParser(enable_hierarchical_splitting=True)
        
        content = """# 主标题

介绍性文字。

## 第一节

第一节的内容。

### 1.1 小节

小节内容。

## 第二节

第二节的内容。"""
        
        chunks = parser._split_by_headings(content)
        
        assert len(chunks) >= 2  # 至少应该有 ## 级别的块
        # 检查是否有标题信息
        assert any(chunk['heading_level'] == 2 for chunk in chunks)
    
    @pytest.mark.skip(reason="需要实际的 Markdown 文件")
    def test_parse_md_with_hierarchy(self):
        """测试解析 Markdown 并使用层级分块"""
        md_path = Path("data/fault_cases.md")
        if not md_path.exists():
            pytest.skip("Markdown 文件不存在")
        
        parser = MarkdownParser(enable_hierarchical_splitting=True)
        documents = parser.parse(str(md_path))
        
        assert len(documents) > 0
        # 检查是否包含标题层级信息
        has_heading_info = any('heading_level' in doc.metadata for doc in documents)
        assert has_heading_info is True


class TestTextSplitterFormatAware:
    """测试格式感知的分块服务"""
    
    def setup_method(self):
        self.splitter = TextSplitterService()
    
    def test_format_aware_split_pdf(self):
        """测试 PDF 格式优化分块"""
        from langchain_core.documents import Document
        
        docs = [Document(page_content="测试内容" * 50, metadata={"source": "test.pdf"})]
        
        chunks = self.splitter.format_aware_split(docs, source_format="pdf")
        
        assert len(chunks) > 0
        # 检查是否添加了 PDF 优化标记
        assert all(chunk.metadata.get('format_optimized') == 'pdf' for chunk in chunks)
    
    def test_format_aware_split_docx(self):
        """测试 Word 格式优化分块"""
        from langchain_core.documents import Document
        
        docs = [Document(
            page_content="测试内容" * 50,
            metadata={"source": "test.docx", "heading_level": 1, "heading_text": "测试标题"}
        )]
        
        chunks = self.splitter.format_aware_split(docs, source_format="docx")
        
        assert len(chunks) > 0
        # 检查是否保留了标题信息
        assert all('heading_level' in chunk.metadata for chunk in chunks)
    
    def test_format_aware_split_md(self):
        """测试 Markdown 格式优化分块"""
        from langchain_core.documents import Document
        
        docs = [Document(
            page_content="测试内容" * 50,
            metadata={"source": "test.md", "heading_level": 2, "heading_text": "测试章节"}
        )]
        
        chunks = self.splitter.format_aware_split(docs, source_format="md")
        
        assert len(chunks) > 0
        # 检查是否保留了标题信息
        assert all('heading_level' in chunk.metadata for chunk in chunks)
    
    def test_format_aware_split_auto(self):
        """测试自动检测格式分块"""
        from langchain_core.documents import Document
        
        docs = [Document(page_content="测试内容" * 50, metadata={"source": "test.txt"})]
        
        chunks = self.splitter.format_aware_split(docs, source_format="auto")
        
        assert len(chunks) > 0
    
    def test_skip_resplit_for_structured_docs(self):
        """测试对已结构化的文档跳过二次分块"""
        from langchain_core.documents import Document
        
        # 模拟已经按标题分块的文档
        docs = [Document(
            page_content="短内容",
            metadata={"heading_level": 2, "section_index": 0}
        )]
        
        chunks = self.splitter.format_aware_split(docs, source_format="docx")
        
        # 应该直接返回，不进行二次分块
        assert len(chunks) == 1
        assert chunks[0].page_content == "短内容"


class TestIntegration:
    """集成测试：完整流程"""
    
    @pytest.mark.skip(reason="需要实际的文件")
    def test_full_pipeline_pdf(self):
        """测试 PDF 完整处理流程"""
        pdf_path = Path("data/惠普笔记本使用指南.pdf")
        if not pdf_path.exists():
            pytest.skip("PDF 文件不存在")
        
        # 1. 解析
        parser = PDFParser(enable_layout_cleaning=True)
        documents = parser.parse(str(pdf_path))
        
        assert len(documents) > 0
        
        # 2. 分块
        splitter = TextSplitterService()
        chunks = splitter.format_aware_split(documents, source_format="pdf")
        
        assert len(chunks) > 0
        # 检查元数据
        assert all('format_optimized' in chunk.metadata for chunk in chunks)
    
    @pytest.mark.skip(reason="需要实际的文件")
    def test_full_pipeline_docx(self):
        """测试 Word 完整处理流程"""
        docx_path = Path("data/test.docx")
        if not docx_path.exists():
            pytest.skip("Word 文件不存在")
        
        # 1. 解析
        parser = DOCXParser(enable_structure_extraction=True)
        documents = parser.parse(str(docx_path))
        
        assert len(documents) > 0
        
        # 2. 分块
        splitter = TextSplitterService()
        chunks = splitter.format_aware_split(documents, source_format="docx")
        
        assert len(chunks) > 0
    
    @pytest.mark.skip(reason="需要实际的文件")
    def test_full_pipeline_md(self):
        """测试 Markdown 完整处理流程"""
        md_path = Path("data/fault_cases.md")
        if not md_path.exists():
            pytest.skip("Markdown 文件不存在")
        
        # 1. 解析
        parser = MarkdownParser(enable_hierarchical_splitting=True)
        documents = parser.parse(str(md_path))
        
        assert len(documents) > 0
        
        # 2. 分块
        splitter = TextSplitterService()
        chunks = splitter.format_aware_split(documents, source_format="md")
        
        assert len(chunks) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
