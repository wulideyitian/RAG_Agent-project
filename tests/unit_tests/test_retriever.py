"""
检索服务单元测试
测试 RetrieverService 的各项功能
"""
import pytest
from unittest.mock import Mock, patch
from langchain_core.documents import Document


class TestRetrieverService:
    """RetrieverService 测试类"""
    
    @pytest.fixture
    def retriever_service(self):
        """初始化检索服务（完全 mock）"""
        with patch('core.rag.retriever.VectorStoreService'):
            from core.rag.retriever import RetrieverService
            
            service = RetrieverService()
            
            # Mock retriever
            mock_retriever = Mock()
            service.retriever = mock_retriever
            
            yield service
    
    def test_init(self, retriever_service):
        """测试初始化"""
        assert retriever_service.vector_store is not None
        assert retriever_service.retriever is not None
    
    def test_retrieve_default_k(self, retriever_service):
        """测试默认 k 值检索"""
        mock_docs = [
            Document(page_content="文档 1", metadata={"source": "test1"}),
            Document(page_content="文档 2", metadata={"source": "test2"}),
        ]
        retriever_service.retriever.invoke.return_value = mock_docs
        
        query = "测试查询"
        results = retriever_service.retrieve(query)
        
        assert len(results) == 2
        assert all(isinstance(doc, Document) for doc in results)
        retriever_service.retriever.invoke.assert_called_once_with(query)
    
    def test_retrieve_custom_k(self, retriever_service):
        """测试自定义 k 值检索"""
        mock_docs = [
            Document(page_content=f"文档{i}", metadata={"source": f"test{i}"})
            for i in range(5)
        ]
        retriever_service.retriever.invoke.return_value = mock_docs
        retriever_service.retriever.search_kwargs = {"k": 3}
        
        query = "测试查询"
        results = retriever_service.retrieve(query, k=5)
        
        assert len(results) == 5
        # k 值应该被临时修改后恢复
    
    def test_retrieve_empty_results(self, retriever_service):
        """测试空检索结果"""
        retriever_service.retriever.invoke.return_value = []
        
        query = "无匹配查询"
        results = retriever_service.retrieve(query)
        
        assert len(results) == 0
        assert results == []
    
    def test_retrieve_error_handling(self, retriever_service):
        """测试检索异常处理"""
        retriever_service.retriever.invoke.side_effect = Exception("检索失败")
        
        query = "测试查询"
        
        with pytest.raises(Exception) as exc_info:
            retriever_service.retrieve(query)
        
        assert "检索失败" in str(exc_info.value)
    
    def test_retrieve_preserves_k_after_custom(self, retriever_service):
        """测试自定义 k 值后恢复原始值"""
        original_k = 3
        retriever_service.retriever.search_kwargs = {"k": original_k}
        retriever_service.retriever.invoke.return_value = []
        
        query = "测试"
        retriever_service.retrieve(query, k=10)
        
        # k 值应该恢复
        assert retriever_service.retriever.search_kwargs["k"] == original_k
    
    def test_retrieve_with_scores(self, retriever_service):
        """测试带相似度分数检索"""
        mock_docs = [
            (Document(page_content="文档 1", metadata={"source": "test1"}), 0.95),
            (Document(page_content="文档 2", metadata={"source": "test2"}), 0.87),
        ]
        retriever_service.vector_store.vector_store.similarity_search_with_score.return_value = mock_docs
        
        query = "测试查询"
        results = retriever_service.retrieve_with_scores(query)
        
        assert len(results) == 2
        assert all(isinstance(item, tuple) for item in results)
        assert all(len(item) == 2 for item in results)
        
        # 验证返回的文档和分数
        first_doc, first_score = results[0]
        assert isinstance(first_doc, Document)
        assert first_score == 0.95
    
    def test_retrieve_with_scores_empty(self, retriever_service):
        """测试带分数检索空结果"""
        retriever_service.vector_store.vector_store.similarity_search_with_score.return_value = []
        
        query = "无匹配查询"
        results = retriever_service.retrieve_with_scores(query)
        
        assert len(results) == 0
        assert results == []
    
    def test_retrieve_with_scores_error(self, retriever_service):
        """测试带分数检索异常"""
        retriever_service.vector_store.vector_store.similarity_search_with_score.side_effect = Exception("检索失败")
        
        query = "测试查询"
        
        with pytest.raises(Exception) as exc_info:
            retriever_service.retrieve_with_scores(query)
        
        assert "带分数检索失败" in str(exc_info.value)
    
    def test_multiple_retrieve_calls(self, retriever_service):
        """测试多次检索调用"""
        mock_docs = [Document(page_content="文档", metadata={"source": "test"})]
        retriever_service.retriever.invoke.return_value = mock_docs
        
        queries = ["查询 1", "查询 2", "查询 3"]
        
        for query in queries:
            result = retriever_service.retrieve(query)
            assert len(result) == 1
        
        assert retriever_service.retriever.invoke.call_count == 3
    
    def test_retrieve_different_k_values(self, retriever_service):
        """测试不同 k 值的检索"""
        retriever_service.retriever.search_kwargs = {"k": 3}
        retriever_service.retriever.invoke.return_value = []
        
        retriever_service.retrieve("查询 1", k=1)
        retriever_service.retrieve("查询 2", k=5)
        retriever_service.retrieve("查询 3", k=10)
        
        # 每次都应临时修改 k 值
    
    def test_document_metadata_access(self, retriever_service):
        """测试检索结果元数据访问"""
        mock_docs = [
            Document(
                page_content="内容",
                metadata={"source": "test.pdf", "page": 1, "file_type": "pdf"}
            ),
        ]
        retriever_service.retriever.invoke.return_value = mock_docs
        
        results = retriever_service.retrieve("测试")
        
        assert results[0].metadata["source"] == "test.pdf"
        assert results[0].metadata["page"] == 1
        assert results[0].metadata["file_type"] == "pdf"
