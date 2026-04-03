"""
嵌入模型服务单元测试
测试 EmbedModelService 的各项功能
"""
import pytest
from unittest.mock import Mock, patch
from core.embedding.embed_model import EmbedModelService


class TestEmbedModelService:
    """EmbedModelService 测试类"""
    
    @pytest.fixture
    def embed_service(self):
        """初始化嵌入服务（使用 mock）"""
        with patch('core.embedding.embed_model.DashScopeEmbeddings'):
            service = EmbedModelService()
            yield service
    
    def test_init(self, embed_service):
        """测试初始化"""
        assert embed_service.model_name is not None
        assert embed_service._model is None  # 懒加载，初始应为 None
    
    def test_model_lazy_loading(self, embed_service):
        """测试模型懒加载"""
        # 首次访问 model 属性时才加载
        with patch.object(embed_service, '_load_model') as mock_load:
            mock_model = Mock()
            mock_load.return_value = mock_model
            
            model = embed_service.model
            
            mock_load.assert_called_once()
            assert model == mock_model
    
    def test_model_property_cached(self, embed_service):
        """测试模型缓存（只加载一次）"""
        with patch.object(embed_service, '_load_model') as mock_load:
            mock_model = Mock()
            mock_load.return_value = mock_model
            
            # 多次访问 model 属性
            _ = embed_service.model
            _ = embed_service.model
            _ = embed_service.model
            
            # 应该只调用一次 _load_model
            mock_load.assert_called_once()
    
    def test_load_model_success(self, embed_service):
        """测试模型加载成功"""
        with patch('core.embedding.embed_model.DashScopeEmbeddings') as mock_dashscope:
            mock_model = Mock()
            mock_dashscope.return_value = mock_model
            
            loaded_model = embed_service._load_model()
            
            mock_dashscope.assert_called_once()
            assert loaded_model == mock_model
    
    def test_load_model_failure(self, embed_service):
        """测试模型加载失败"""
        with patch('core.embedding.embed_model.DashScopeEmbeddings') as mock_dashscope:
            mock_dashscope.side_effect = Exception("加载失败")
            
            with pytest.raises(RuntimeError) as exc_info:
                embed_service._load_model()
            
            assert "加载嵌入模型失败" in str(exc_info.value)
    
    def test_embed_documents(self, embed_service):
        """测试文档列表向量化"""
        mock_model = Mock()
        mock_model.embed_documents.return_value = [[0.1, 0.2], [0.3, 0.4]]
        embed_service._model = mock_model
        
        texts = ["文本一", "文本二"]
        embeddings = embed_service.embed_documents(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 2
        assert len(embeddings[1]) == 2
        mock_model.embed_documents.assert_called_once_with(texts)
    
    def test_embed_query(self, embed_service):
        """测试查询文本向量化"""
        mock_model = Mock()
        mock_model.embed_query.return_value = [0.5, 0.6]
        embed_service._model = mock_model
        
        text = "查询文本"
        embedding = embed_service.embed_query(text)
        
        assert len(embedding) == 2
        assert embedding == [0.5, 0.6]
        mock_model.embed_query.assert_called_once_with(text)
    
    def test_embed_empty_list(self, embed_service):
        """测试空列表向量化"""
        mock_model = Mock()
        mock_model.embed_documents.return_value = []
        embed_service._model = mock_model
        
        texts = []
        embeddings = embed_service.embed_documents(texts)
        
        assert embeddings == []
    
    def test_embed_single_document(self, embed_service):
        """测试单个文档向量化"""
        mock_model = Mock()
        mock_model.embed_documents.return_value = [[0.7, 0.8]]
        embed_service._model = mock_model
        
        texts = ["单个文本"]
        embeddings = embed_service.embed_documents(texts)
        
        assert len(embeddings) == 1
    
    def test_embed_long_text(self, embed_service):
        """测试长文本向量化"""
        mock_model = Mock()
        mock_model.embed_query.return_value = [0.9] * 1536  # 模拟高维向量
        embed_service._model = mock_model
        
        long_text = "这是一个很长的文本。" * 100
        embedding = embed_service.embed_query(long_text)
        
        assert len(embedding) > 0
    
    def test_embed_multiple_queries(self, embed_service):
        """测试多次查询向量化"""
        mock_model = Mock()
        mock_model.embed_query.side_effect = [
            [0.1, 0.2],
            [0.3, 0.4],
            [0.5, 0.6]
        ]
        embed_service._model = mock_model
        
        queries = ["查询 1", "查询 2", "查询 3"]
        results = [embed_service.embed_query(q) for q in queries]
        
        assert len(results) == 3
        assert mock_model.embed_query.call_count == 3
    
    def test_model_name_from_config(self):
        """测试从配置读取模型名称"""
        with patch('core.embedding.embed_model.rag_conf') as mock_config:
            mock_config.get.return_value = "custom-embedding-model"
            
            with patch('core.embedding.embed_model.DashScopeEmbeddings'):
                service = EmbedModelService()
                
                assert service.model_name == "custom-embedding-model"
    
    def test_default_model_name(self, embed_service):
        """测试默认模型名称"""
        # 如果配置中没有指定，应使用默认值
        assert embed_service.model_name in ["text-embedding-v2", "text-embedding-v1", "text-embedding-v4"]
