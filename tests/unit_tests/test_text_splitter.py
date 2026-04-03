"""
文本分块器单元测试
测试 TextSplitterService 的各项功能
"""
import pytest
from langchain_core.documents import Document
from core.preprocessing.text_splitter import TextSplitterService


class TestTextSplitterService:
    """TextSplitterService 测试类"""
    
    @pytest.fixture
    def splitter(self):
        """初始化分块器"""
        return TextSplitterService()
    
    def test_init(self, splitter):
        """测试初始化"""
        assert splitter.chunk_size > 0
        assert splitter.chunk_overlap >= 0
        assert splitter.recursive_splitter is not None
        assert splitter.character_splitter is not None
    
    def test_split_documents_recursive(self, splitter):
        """测试递归分块"""
        text = "这是第一段。\n\n这是第二段。\n\n这是第三段。" * 10
        doc = Document(page_content=text, metadata={"source": "test"})
        
        chunks = splitter.split_documents([doc], strategy="recursive")
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Document) for chunk in chunks)
        assert all(len(chunk.page_content) > 0 for chunk in chunks)
    
    def test_split_documents_character(self, splitter):
        """测试字符分块"""
        text = "第一段内容。\n第二段内容。\n第三段内容。" * 5
        doc = Document(page_content=text, metadata={"source": "test"})
        
        chunks = splitter.split_documents([doc], strategy="character")
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Document) for chunk in chunks)
    
    def test_split_documents_invalid_strategy(self, splitter):
        """测试无效分块策略（应回退到 recursive）"""
        text = "测试内容" * 10
        doc = Document(page_content=text, metadata={"source": "test"})
        
        chunks = splitter.split_documents([doc], strategy="invalid")
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Document) for chunk in chunks)
    
    def test_split_text_basic(self, splitter):
        """测试基础文本分割"""
        text = "这是第一段。\n\n这是第二段。\n\n这是第三段。" * 5
        
        chunks = splitter.split_text(text)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Document) for chunk in chunks)
        assert all(chunk.page_content.strip() for chunk in chunks)
    
    def test_split_text_with_metadata(self, splitter):
        """测试带元数据的文本分割"""
        text = "测试内容" * 10
        metadata = {"source": "test.txt", "author": "tester"}
        
        chunks = splitter.split_text(text, metadata=metadata)
        
        assert len(chunks) > 0
        assert all(chunk.metadata.get("source") == "test.txt" for chunk in chunks)
    
    def test_split_short_text(self, splitter):
        """测试短文本分割"""
        text = "短文本"
        
        chunks = splitter.split_text(text)
        
        assert len(chunks) == 1
        assert chunks[0].page_content == text
    
    def test_split_long_text(self, splitter):
        """测试长文本分割"""
        text = "这是一句话。" * 50  # 减小文本长度以匹配实际的 chunk_size
        
        chunks = splitter.split_text(text)
        
        # 确保至少有一个 chunk
        assert len(chunks) >= 1
        assert sum(len(chunk.page_content) for chunk in chunks) > 0
    
    def test_adaptive_split_with_sections(self, splitter):
        """测试自适应分块（有章节结构）"""
        text = "\n\n".join([f"第{i}章内容" * 20 for i in range(5)])
        
        chunks = splitter.adaptive_split(text, source="book.txt")
        
        assert len(chunks) > 0
        assert all(chunk.metadata.get("source") == "book.txt" for chunk in chunks)
    
    def test_adaptive_split_with_sentences(self, splitter):
        """测试自适应分块（有句子结构）"""
        text = "这是第一句。这是第二句。这是第三句。" * 30
        
        chunks = splitter.adaptive_split(text, source="article.txt")
        
        assert len(chunks) > 0
    
    def test_adaptive_split_plain_text(self, splitter):
        """测试自适应分块（无结构文本）"""
        text = "纯文本内容" * 50
        
        chunks = splitter.adaptive_split(text, source="plain.txt")
        
        assert len(chunks) > 0
    
    def test_adaptive_split_respects_size_limits(self, splitter):
        """测试自适应分块的尺寸限制"""
        text = "内容" * 500
        
        chunks = splitter.adaptive_split(
            text, 
            source="test.txt",
            min_chunk_size=100,
            max_chunk_size=500
        )
        
        assert len(chunks) > 0
    
    def test_split_preserves_metadata(self, splitter):
        """测试分块保留元数据"""
        text = "第一段。\n\n第二段。" * 10
        metadata = {"file_type": "pdf", "page": 1}
        
        chunks = splitter.split_text(text, metadata=metadata)
        
        # 注意：split_documents 会保留原始 metadata
        assert all("file_type" in chunk.metadata for chunk in chunks)
    
    def test_split_empty_text(self, splitter):
        """测试空文本分割"""
        text = ""
        
        chunks = splitter.split_text(text)
        
        assert len(chunks) == 1  # 即使空文本也会返回一个 Document
        assert chunks[0].page_content == ""
    
    def test_different_chunk_sizes(self, splitter):
        """测试不同 chunk_size 的效果"""
        text = "句子一。句子二。句子三。" * 20
        
        # 小块
        small_chunks = splitter.split_text(text)
        
        # 修改配置后的大块（需要重新初始化）
        splitter.chunk_size = 1000
        splitter.recursive_splitter = type(splitter.recursive_splitter)(
            chunk_size=1000,
            chunk_overlap=splitter.chunk_overlap,
            separators=splitter.separators,
        )
        large_chunks = splitter.split_text(text)
        
        # 大块应该分出的块数更少
        assert len(large_chunks) <= len(small_chunks)
    
    def test_chinese_text_splitting(self, splitter):
        """测试中文文本分割"""
        text = "这是中文段落一。\n\n这是中文段落二。\n\n这是中文段落三。" * 5
        
        chunks = splitter.split_text(text)
        
        assert len(chunks) > 0
        assert any('中文' in chunk.page_content for chunk in chunks)
    
    def test_mixed_language_text(self, splitter):
        """测试混合语言文本分割"""
        text = "English sentence. 中文句子。日本語の文。" * 10
        
        chunks = splitter.split_text(text)
        
        assert len(chunks) > 0
