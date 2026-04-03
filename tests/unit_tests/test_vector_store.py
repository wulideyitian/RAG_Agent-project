"""
向量库服务单元测试
测试 VectorStoreService 的各项功能
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os


class TestVectorStoreService:
    """VectorStoreService 测试类"""
    
    @pytest.fixture
    def vector_store_service(self):
        """初始化向量库服务（完全 mock）"""
        with patch('core.rag.vector_store.Chroma'):
            with patch('core.rag.vector_store.EmbedModelService'):
                with patch('core.rag.vector_store.TextSplitterService'):
                    with patch('core.rag.vector_store.UnifiedDocumentLoader'):
                        from core.rag.vector_store import VectorStoreService
                        service = VectorStoreService()
                        yield service
    
    def test_init(self, vector_store_service):
        """测试初始化"""
        assert vector_store_service.embed_service is not None
        assert vector_store_service.spliter is not None
        assert vector_store_service.doc_loader is not None
        assert vector_store_service.vector_store is not None
    
    def test_get_retriever(self, vector_store_service):
        """测试获取检索器"""
        mock_retriever = Mock()
        vector_store_service.vector_store.as_retriever.return_value = mock_retriever
        
        retriever = vector_store_service.get_retriever()
        
        vector_store_service.vector_store.as_retriever.assert_called_once()
        assert retriever == mock_retriever
    
    def test_load_documents(self, vector_store_service):
        """测试加载文档到向量库"""
        # Mock 文件列表
        mock_files = ["/path/to/doc1.txt", "/path/to/doc2.pdf"]
        
        with patch('core.rag.vector_store.listdir_with_allowed_type') as mock_listdir:
            mock_listdir.return_value = mock_files
            
            with patch.object(vector_store_service, '_load_single_document') as mock_load_doc:
                vector_store_service.load_documents()
                
                mock_listdir.assert_called_once()
                assert mock_load_doc.call_count == len(mock_files)
    
    def test_load_single_document_success(self, vector_store_service):
        """测试加载单个文档成功"""
        filepath = "/test/doc.txt"
        
        # Mock MD5 检查
        with patch.object(vector_store_service, '_check_md5_exists') as mock_check_md5:
            mock_check_md5.return_value = False
            
            # Mock 文档加载
            with patch.object(vector_store_service.doc_loader, 'load_from_path') as mock_loader:
                mock_loader.return_value = {
                    "text": "测试内容",
                    "file_type": "txt",
                    "status": "success",
                    "error_msg": ""
                }
                
                # Mock MD5 获取
                with patch('core.rag.vector_store.get_file_md5_hex') as mock_md5:
                    mock_md5.return_value = "abc123"
                    
                    # Mock 分块
                    with patch.object(vector_store_service.spliter, 'split_documents') as mock_split:
                        mock_chunk = Mock()
                        mock_split.return_value = [mock_chunk]
                        
                        # Mock 向量库添加
                        with patch.object(vector_store_service.vector_store, 'add_documents') as mock_add:
                            # Mock MD5 保存
                            with patch.object(vector_store_service, '_save_md5') as mock_save:
                                vector_store_service._load_single_document(filepath)
                                
                                mock_check_md5.assert_called_once()
                                mock_loader.assert_called_once_with(filepath)
                                mock_split.assert_called_once()
                                mock_add.assert_called_once()
                                mock_save.assert_called_once()
    
    def test_load_single_document_already_processed(self, vector_store_service):
        """测试已处理过的文档（MD5 存在）"""
        filepath = "/test/doc.txt"
        
        with patch.object(vector_store_service, '_check_md5_exists') as mock_check_md5:
            mock_check_md5.return_value = True
            
            with patch('core.rag.vector_store.get_file_md5_hex') as mock_md5:
                vector_store_service._load_single_document(filepath)
                
                mock_check_md5.assert_called_once()
                # 不应该继续加载
    
    def test_load_single_document_empty_content(self, vector_store_service):
        """测试空内容文档"""
        filepath = "/test/empty.txt"
        
        with patch.object(vector_store_service, '_check_md5_exists') as mock_check_md5:
            mock_check_md5.return_value = False
            
            with patch.object(vector_store_service.doc_loader, 'load_from_path') as mock_loader:
                mock_loader.return_value = {
                    "text": "",
                    "file_type": "txt",
                    "status": "warning",
                    "error_msg": "未提取到有效内容"
                }
                
                with patch('core.rag.vector_store.get_file_md5_hex'):
                    vector_store_service._load_single_document(filepath)
                    
                    # 不应该调用 split_documents 和 add_documents
    
    def test_load_single_document_failed_splitting(self, vector_store_service):
        """测试分块失败"""
        filepath = "/test/doc.txt"
        
        with patch.object(vector_store_service, '_check_md5_exists') as mock_check_md5:
            mock_check_md5.return_value = False
            
            with patch.object(vector_store_service.doc_loader, 'load_from_path') as mock_loader:
                mock_loader.return_value = {
                    "text": "有内容但分块失败",
                    "file_type": "txt",
                    "status": "success",
                    "error_msg": ""
                }
                
                with patch('core.rag.vector_store.get_file_md5_hex'):
                    with patch.object(vector_store_service.spliter, 'split_documents') as mock_split:
                        mock_split.return_value = []  # 分块后为空
                        
                        vector_store_service._load_single_document(filepath)
                        
                        # 不应该调用 add_documents
    
    def test_load_single_document_error_handling(self, vector_store_service):
        """测试异常处理"""
        filepath = "/test/error.txt"
        
        with patch.object(vector_store_service, '_check_md5_exists') as mock_check_md5:
            mock_check_md5.return_value = False
            
            with patch.object(vector_store_service.doc_loader, 'load_from_path') as mock_loader:
                mock_loader.side_effect = Exception("加载失败")
                
                # 应该捕获异常，不抛出
                vector_store_service._load_single_document(filepath)
    
    def test_check_md5_exists_true(self, vector_store_service, tmp_path):
        """测试 MD5 存在性检查（存在）"""
        md5_file = tmp_path / "md5.txt"
        md5_file.write_text("abc123\ndef456\n")
        
        with patch('core.rag.vector_store.get_abs_path') as mock_abs:
            mock_abs.return_value = str(md5_file)
            
            result = vector_store_service._check_md5_exists("abc123")
            
            assert result is True
    
    def test_check_md5_exists_false(self, vector_store_service, tmp_path):
        """测试 MD5 存在性检查（不存在）"""
        md5_file = tmp_path / "md5.txt"
        md5_file.write_text("abc123\ndef456\n")
        
        with patch('core.rag.vector_store.get_abs_path') as mock_abs:
            mock_abs.return_value = str(md5_file)
            
            result = vector_store_service._check_md5_exists("xyz789")
            
            assert result is False
    
    def test_check_md5_file_not_exists(self, vector_store_service, tmp_path):
        """测试 MD5 文件不存在"""
        md5_file = tmp_path / "nonexistent.txt"
        
        with patch('core.rag.vector_store.get_abs_path') as mock_abs:
            mock_abs.return_value = str(md5_file)
            
            result = vector_store_service._check_md5_exists("any_md5")
            
            assert result is False
    
    def test_save_md5(self, vector_store_service, tmp_path):
        """测试保存 MD5"""
        md5_file = tmp_path / "md5.txt"
        
        with patch('core.rag.vector_store.get_abs_path') as mock_abs:
            mock_abs.return_value = str(md5_file)
            
            vector_store_service._save_md5("new_md5_value")
            
            content = md5_file.read_text()
            assert "new_md5_value" in content
    
    def test_save_multiple_md5(self, vector_store_service, tmp_path):
        """测试保存多个 MD5"""
        md5_file = tmp_path / "md5.txt"
        
        with patch('core.rag.vector_store.get_abs_path') as mock_abs:
            mock_abs.return_value = str(md5_file)
            
            vector_store_service._save_md5("md5_1")
            vector_store_service._save_md5("md5_2")
            vector_store_service._save_md5("md5_3")
            
            lines = md5_file.read_text().strip().split('\n')
            assert len(lines) == 3
            assert "md5_1" in lines
            assert "md5_2" in lines
            assert "md5_3" in lines
