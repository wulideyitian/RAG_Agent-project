"""
分块质量检查器单元测试
测试 QualityChecker 的各项功能
"""
import pytest
from langchain_core.documents import Document
from core.preprocessing.quality_checker import QualityChecker


class TestQualityChecker:
    """QualityChecker 测试类"""
    
    @pytest.fixture
    def checker(self):
        """初始化质量检查器"""
        return QualityChecker()
    
    def test_init(self, checker):
        """测试初始化"""
        assert checker.min_chunk_length == 50
        assert checker.max_chunk_length == 2000
        assert checker.similarity_threshold == 0.9
    
    def test_check_length_short(self, checker):
        """测试长度检查 - 太短"""
        text = "短句"
        result = checker._check_length(text)
        assert result is False
    
    def test_check_length_good(self, checker):
        """测试长度检查 - 合格"""
        text = "这是一段长度合适的文本，" * 10
        result = checker._check_length(text)
        assert result is True
    
    def test_check_length_too_long(self, checker):
        """测试长度检查 - 太长"""
        text = "这是一段非常长的文本，" * 1000
        result = checker._check_length(text)
        assert result is False
    
    def test_check_length_boundary(self, checker):
        """测试长度边界值"""
        # 刚好等于最小长度
        min_text = "x" * 50
        result = checker._check_length(min_text)
        assert result is True
        
        # 刚好等于最大长度
        max_text = "y" * 2000
        result = checker._check_length(max_text)
        assert result is True
        
        # 比最小长度少 1
        short_text = "z" * 49
        result = checker._check_length(short_text)
        assert result is False
        
        # 比最大长度多 1
        long_text = "w" * 2001
        result = checker._check_length(long_text)
        assert result is False
    
    def test_check_content_quality_good(self, checker):
        """测试内容质量 - 合格"""
        text = "这是一段正常的文本。它包含完整的句子和标点符号。内容也很有意义。"
        result = checker._check_content_quality(text)
        assert result is True
    
    def test_check_content_quality_empty(self, checker):
        """测试内容质量 - 空文本"""
        result = checker._check_content_quality("")
        assert result is False
    
    def test_check_content_quality_special_chars(self, checker):
        """测试内容质量 - 特殊字符过多"""
        text = "@#$%^&*" * 20
        result = checker._check_content_quality(text)
        assert result is False
    
    def test_check_content_quality_no_sentence(self, checker):
        """测试内容质量 - 没有完整句子"""
        text = "这是一个没有标点符号的长字符串它没有任何停顿也没有分隔符就是连续的字符"
        result = checker._check_content_quality(text)
        assert result is False
    
    def test_check_content_quality_with_punctuation(self, checker):
        """测试内容质量 - 有标点符号"""
        text = "这是第一句，这是第二句；这是第三句！这是第四句？"
        result = checker._check_content_quality(text)
        assert result is True
    
    def test_is_duplicate_identical(self, checker):
        """测试重复检测 - 完全相同"""
        content = "这是测试文本" * 10
        chunk1 = Document(page_content=content, metadata={})
        chunk2 = Document(page_content=content, metadata={})
        
        result = checker._is_duplicate(chunk1, chunk2)
        assert result is True
    
    def test_is_duplicate_similar(self, checker):
        """测试重复检测 - 高度相似"""
        content1 = "这是测试文本" * 10
        content2 = "这是测试文本" * 9 + "这是修改的文本"
        
        chunk1 = Document(page_content=content1, metadata={})
        chunk2 = Document(page_content=content2, metadata={})
        
        result = checker._is_duplicate(chunk1, chunk2)
        assert result is True
    
    def test_is_duplicate_different(self, checker):
        """测试重复检测 - 不同内容"""
        content1 = "这是第一段完全不同的内容"
        content2 = "这是第二段完全不同的内容"
        
        chunk1 = Document(page_content=content1, metadata={})
        chunk2 = Document(page_content=content2, metadata={})
        
        result = checker._is_duplicate(chunk1, chunk2)
        assert result is False
    
    def test_is_duplicate_one_empty(self, checker):
        """测试重复检测 - 一个为空"""
        chunk1 = Document(page_content="", metadata={})
        chunk2 = Document(page_content="测试内容", metadata={})
        
        result = checker._is_duplicate(chunk1, chunk2)
        assert result is False
    
    def test_is_duplicate_both_empty(self, checker):
        """测试重复检测 - 都为空"""
        chunk1 = Document(page_content="", metadata={})
        chunk2 = Document(page_content="", metadata={})
        
        result = checker._is_duplicate(chunk1, chunk2)
        assert result is False
    
    def test_check_chunks_all_valid(self, checker):
        """测试检查分块 - 全部合格"""
        chunks = [
            Document(page_content="这是第一段合格的文本。" * 10, metadata={"id": 1}),
            Document(page_content="这是第二段合格的文本。" * 10, metadata={"id": 2}),
            Document(page_content="这是第三段合格的文本。" * 10, metadata={"id": 3}),
        ]
        
        result = checker.check_chunks(chunks)
        
        assert len(result) == 3
        assert all(chunk.metadata["id"] in [1, 2, 3] for chunk in result)
    
    def test_check_chunks_filter_short(self, checker):
        """测试检查分块 - 过滤太短的"""
        chunks = [
            Document(page_content="这是合格的文本。" * 10, metadata={"id": 1}),
            Document(page_content="短句", metadata={"id": 2}),  # 太短
            Document(page_content="这是另一段合格的文本。" * 10, metadata={"id": 3}),
        ]
        
        result = checker.check_chunks(chunks)
        
        assert len(result) == 2
        assert result[0].metadata["id"] == 1
        assert result[1].metadata["id"] == 3
    
    def test_check_chunks_filter_duplicates(self, checker):
        """测试检查分块 - 过滤重复的"""
        same_content = "这是重复的文本" * 10
        
        chunks = [
            Document(page_content=same_content, metadata={"id": 1}),
            Document(page_content=same_content, metadata={"id": 2}),  # 重复
            Document(page_content="这是不同的内容" * 10, metadata={"id": 3}),
        ]
        
        result = checker.check_chunks(chunks)
        
        assert len(result) == 2
        assert result[0].metadata["id"] == 1
        assert result[1].metadata["id"] == 3
    
    def test_check_chunks_mixed_issues(self, checker):
        """测试检查分块 - 混合问题"""
        chunks = [
            Document(page_content="合格文本" * 10, metadata={"id": 1}),
            Document(page_content="太短", metadata={"id": 2}),  # 太短
            Document(page_content="特殊@#$%" * 20, metadata={"id": 3}),  # 质量差
            Document(page_content="合格文本" * 10, metadata={"id": 4}),  # 与 1 不重复（超过比较长度）
        ]
        
        result = checker.check_chunks(chunks)
        
        # 至少应该有 2 个合格（id=1 和 id=4）
        assert len(result) >= 2
    
    def test_optimize_chunks_merge_small(self, checker):
        """测试优化分块 - 合并小块"""
        small_chunk1 = Document(page_content="小段落 1" * 5, metadata={"source": "doc1"})
        small_chunk2 = Document(page_content="小段落 2" * 5, metadata={"source": "doc2"})
        
        chunks = [small_chunk1, small_chunk2]
        
        result = checker.optimize_chunks(chunks)
        
        # 两个小块应该被合并
        assert len(result) == 1
        assert "小段落 1" in result[0].page_content
        assert "小段落 2" in result[0].page_content
    
    def test_optimize_chunks_keep_good(self, checker):
        """测试优化分块 - 保留合格分块"""
        good_chunk = Document(page_content="合格段落" * 20, metadata={"id": 1})
        
        chunks = [good_chunk]
        
        result = checker.optimize_chunks(chunks)
        
        assert len(result) == 1
        assert result[0].metadata["id"] == 1
    
    def test_optimize_chunks_split_large(self, checker):
        """测试优化分块 - 处理大块"""
        # 创建一个超过最大长度的分块
        large_content = "内容" * 1000  # 远超过 2000 字符
        large_chunk = Document(page_content=large_content, metadata={"id": 1})
        
        chunks = [large_chunk]
        
        result = checker.optimize_chunks(chunks)
        
        # 大块不会被拆分（当前实现只合并，不拆分）
        assert len(result) == 1
    
    def test_optimize_chunks_complex(self, checker):
        """测试优化分块 - 复杂场景"""
        chunks = [
            Document(page_content="小 1" * 10, metadata={"id": 1}),  # 小
            Document(page_content="中 1" * 30, metadata={"id": 2}),  # 中等
            Document(page_content="小 2" * 10, metadata={"id": 3}),  # 小
            Document(page_content="小 3" * 10, metadata={"id": 4}),  # 小
        ]
        
        result = checker.optimize_chunks(chunks)
        
        # 验证优化结果
        assert len(result) > 0
        # 所有原始内容都应该在结果中
        all_content = "\n\n".join([chunk.page_content for chunk in result])
        assert "小 1" in all_content
        assert "中 1" in all_content
        assert "小 2" in all_content
        assert "小 3" in all_content
    
    def test_optimize_chunks_empty_list(self, checker):
        """测试优化分块 - 空列表"""
        result = checker.optimize_chunks([])
        assert result == []
    
    def test_check_and_optimize_workflow(self, checker):
        """测试检查 + 优化完整流程"""
        # 创建混合质量的分块
        chunks = [
            Document(page_content="优质内容" * 20, metadata={"seq": 1}),
            Document(page_content="短", metadata={"seq": 2}),  # 太短
            Document(page_content="另一个优质内容" * 20, metadata={"seq": 3}),
            Document(page_content="小小小" * 5, metadata={"seq": 4}),  # 小
        ]
        
        # 先检查质量
        valid_chunks = checker.check_chunks(chunks)
        
        # 再优化
        optimized_chunks = checker.optimize_chunks(valid_chunks)
        
        # 验证结果
        assert len(optimized_chunks) <= len(chunks)
        assert len(optimized_chunks) > 0
    
    def test_checker_with_metadata(self, checker):
        """测试检查器保留元数据"""
        chunks = [
            Document(
                page_content="测试内容" * 20, 
                metadata={"source": "test.txt", "page": 1, "author": "test"}
            ),
        ]
        
        result = checker.check_chunks(chunks)
        
        assert len(result) == 1
        assert result[0].metadata["source"] == "test.txt"
        assert result[0].metadata["page"] == 1
        assert result[0].metadata["author"] == "test"
