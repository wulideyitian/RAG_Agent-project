"""
统一文档加载器单元测试
测试 UnifiedDocumentLoader 的各项功能
"""
import pytest
import os
import tempfile
from core.loader.document_loader import UnifiedDocumentLoader


class TestUnifiedDocumentLoader:
    """UnifiedDocumentLoader 测试类"""
    
    @pytest.fixture
    def loader(self):
        """初始化加载器"""
        return UnifiedDocumentLoader()
    
    @pytest.fixture
    def sample_txt_file(self):
        """创建临时 TXT 测试文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("这是测试文本内容。\n包含多行文本。")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
    
    @pytest.fixture
    def sample_md_file(self):
        """创建临时 Markdown 测试文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# 测试标题\n\n这是测试内容。")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
    
    def test_init(self, loader):
        """测试初始化"""
        assert loader.parsers is not None
        assert 'pdf' in loader.parsers
        assert 'txt' in loader.parsers
        assert 'docx' in loader.parsers
        assert 'md' in loader.parsers
    
    def test_detect_file_type_txt(self, loader, sample_txt_file):
        """测试 TXT 文件类型检测"""
        file_type = loader._detect_file_type(sample_txt_file)
        assert file_type == 'txt'
    
    def test_detect_file_type_md(self, loader, sample_md_file):
        """测试 Markdown 文件类型检测"""
        file_type = loader._detect_file_type(sample_md_file)
        assert file_type == 'md'
    
    def test_load_from_path_txt_success(self, loader, sample_txt_file):
        """测试从路径加载 TXT 文件"""
        result = loader.load_from_path(sample_txt_file)
        
        assert result['status'] == 'success'
        assert result['file_type'] == 'txt'
        assert '测试文本' in result['text']
        assert result['error_msg'] == ''
    
    def test_load_from_path_md_success(self, loader, sample_md_file):
        """测试从路径加载 Markdown 文件"""
        result = loader.load_from_path(sample_md_file)
        
        assert result['status'] == 'success'
        assert result['file_type'] == 'md'
        assert '测试标题' in result['text']
        assert result['error_msg'] == ''
    
    def test_load_from_path_not_exist(self, loader):
        """测试加载不存在的文件"""
        result = loader.load_from_path('/non/exist/file.txt')
        
        assert result['status'] == 'error'
        assert 'error_msg' in result
    
    def test_load_from_path_unsupported_type(self, loader, tmp_path):
        """测试加载不支持的文件类型"""
        # 创建一个不支持的文件
        unsupported_file = tmp_path / "test.xyz"
        unsupported_file.write_text("content")
        
        result = loader.load_from_path(str(unsupported_file))
        
        assert result['status'] == 'error'
        assert '不支持' in result['error_msg']
    
    def test_load_from_binary_txt(self, loader):
        """测试从二进制流加载 TXT 文件"""
        binary_data = b"This is test content.\nMultiple lines."
        result = loader.load_from_binary(binary_data, 'txt')
        
        assert result['status'] == 'success'
        assert result['file_type'] == 'txt'
        assert 'test content' in result['text']
    
    def test_load_from_binary_with_chinese(self, loader):
        """测试从二进制流加载中文内容"""
        binary_data = "这是中文测试内容。".encode('utf-8')
        result = loader.load_from_binary(binary_data, 'txt')
        
        assert result['status'] == 'success'
        assert '中文测试' in result['text']
    
    def test_load_from_binary_invalid_type(self, loader):
        """测试从不支持的文件类型加载"""
        binary_data = b"some data"
        result = loader.load_from_binary(binary_data, 'xyz')
        
        assert result['status'] == 'error'
    
    def test_load_empty_file(self, loader, tmp_path):
        """测试加载空文件"""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        
        result = loader.load_from_path(str(empty_file))
        
        assert result['status'] == 'warning'
        assert '未提取到有效内容' in result['error_msg']
    
    def test_load_from_path_pdf_placeholder(self, loader):
        """测试 PDF 文件加载（占位测试，需要实际 PDF 文件）"""
        # 这里使用 data 目录下的真实 PDF 文件
        pdf_path = "data/笔记本使用技巧.txt"  # 先用 TXT 代替
        if os.path.exists(pdf_path):
            result = loader.load_from_path(pdf_path)
            assert result['status'] in ['success', 'warning']
    
    def test_multiple_load_same_file(self, loader, sample_txt_file):
        """测试多次加载同一文件"""
        result1 = loader.load_from_path(sample_txt_file)
        result2 = loader.load_from_path(sample_txt_file)
        
        assert result1['status'] == 'success'
        assert result2['status'] == 'success'
        assert result1['text'] == result2['text']
    
    def test_load_file_with_special_chars_in_path(self, loader, tmp_path):
        """测试加载路径包含特殊字符的文件"""
        special_file = tmp_path / "test file (1).txt"
        special_file.write_text("测试内容", encoding='utf-8')
        
        result = loader.load_from_path(str(special_file))
        
        assert result['status'] == 'success'
        assert '测试内容' in result['text']
