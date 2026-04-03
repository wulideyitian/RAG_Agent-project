"""
RAG 核心模块集成测试
测试完整的 RAG 流程（文档加载 -> 分块 -> 向量化 -> 检索 -> 生成）
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.documents import Document


class TestRAGIntegration:
    """RAG 集成测试类"""
    
    @pytest.fixture
    def mock_rag_pipeline(self):
        """Mock 完整的 RAG 流程"""
        # Mock 所有外部依赖
        with patch('core.rag.generator.ChatTongyi'):
            with patch('core.rag.vector_store.Chroma'):
                with patch('core.rag.vector_store.EmbedModelService'):
                    with patch('core.rag.vector_store.TextSplitterService'):
                        with patch('core.rag.vector_store.UnifiedDocumentLoader'):
                            with patch('core.rag.generator.StrOutputParser'):
                                with patch('core.rag.generator.PromptTemplate'):
                                    from core.rag.generator import RAGGenerator
                                    from core.rag.retriever import RetrieverService
                                    
                                    rag_gen = RAGGenerator()
                                    ret_svc = RetrieverService()
                                    
                                    yield {
                                        'generator': rag_gen,
                                        'retriever': ret_svc,
                                    }
    
    def test_full_rag_flow(self, mock_rag_pipeline):
        """测试完整 RAG 流程"""
        generator = mock_rag_pipeline['generator']
        retriever = mock_rag_pipeline['retriever']
        
        # Mock 检索结果
        retrieved_docs = [
            Document(
                page_content="笔记本开机无反应的解决方法：1.检查电源适配器 2.检查电池",
                metadata={"source": "故障排除.pdf"}
            ),
            Document(
                page_content="如果电源指示灯不亮，可能是主板故障",
                metadata={"source": "硬件手册.pdf"}
            ),
        ]
        retriever.retriever.invoke.return_value = retrieved_docs
        
        # Mock 生成结果
        generator.chain.invoke.return_value = "建议您先检查电源适配器和电池连接..."
        
        # 执行 RAG 流程
        query = "笔记本开机没反应怎么办？"
        context_docs = retriever.retrieve(query)
        response = generator.generate(query, context_docs)
        
        assert len(context_docs) == 2
        assert response is not None
        assert len(response) > 0
    
    def test_document_loading_and_splitting(self):
        """测试文档加载和分块"""
        with patch('core.loader.document_loader.UnifiedDocumentLoader') as MockLoader:
            mock_loader = MockLoader.return_value
            mock_loader.load_from_path.return_value = {
                "text": "这是笔记本使用指南的详细内容。" * 100,
                "file_type": "txt",
                "status": "success",
                "error_msg": ""
            }
            
            from core.loader.document_loader import UnifiedDocumentLoader
            from core.preprocessing.text_splitter import TextSplitterService
            
            loader = UnifiedDocumentLoader()
            splitter = TextSplitterService()
            
            result = loader.load_from_path("test.txt")
            
            assert result['status'] == 'success'
            
            from langchain_core.documents import Document
            doc = Document(page_content=result['text'], metadata={"source": "test.txt"})
            chunks = splitter.split_documents([doc])
            
            assert len(chunks) > 0
    
    def test_retrieval_with_different_k_values(self, mock_rag_pipeline):
        """测试不同 k 值的检索效果"""
        retriever = mock_rag_pipeline['retriever']
        
        for k in [1, 3, 5, 10]:
            mock_docs = [
                Document(page_content=f"内容{i}", metadata={"source": f"doc{i}.pdf"})
                for i in range(k)
            ]
            retriever.retriever.invoke.return_value = mock_docs
            retriever.retriever.search_kwargs = {"k": 3}
            
            results = retriever.retrieve("测试查询", k=k)
            
            assert len(results) == k
    
    def test_context_formatting_quality(self, mock_rag_pipeline):
        """测试上下文格式化质量"""
        generator = mock_rag_pipeline['generator']
        
        docs = [
            Document(
                page_content="重要的技术信息",
                metadata={"source": "tech_manual.pdf", "page": 5}
            ),
            Document(
                page_content="故障排除步骤",
                metadata={"source": "troubleshooting.pdf"}
            ),
        ]
        
        formatted = generator._format_context(docs)
        
        # 验证格式化包含必要信息
        assert "【参考资料 1】" in formatted
        assert "【参考资料 2】" in formatted
        assert "tech_manual.pdf" in formatted
        assert "troubleshooting.pdf" in formatted
        assert "重要的技术信息" in formatted
        assert "故障排除步骤" in formatted
    
    def test_end_to_end_qa_flow(self, mock_rag_pipeline):
        """测试端到端问答流程"""
        generator = mock_rag_pipeline['generator']
        retriever = mock_rag_pipeline['retriever']
        
        # 模拟真实的 RAG 场景
        knowledge_base = [
            Document(
                page_content="""Windows 11 系统重置方法：
                1. 打开设置 > 更新和安全 > 恢复
                2. 点击"开始"按钮在"重置此电脑"下
                3. 选择"保留我的文件"或"删除所有内容""",
                metadata={"source": "windows_guide.pdf"}
            ),
            Document(
                page_content="""BIOS 恢复出厂设置：
                1. 开机时按 F2 进入 BIOS
                2. 找到"Load Setup Defaults"选项
                3. 保存并退出""",
                metadata={"source": "bios_manual.pdf"}
            ),
        ]
        
        retriever.retriever.invoke.return_value = knowledge_base
        generator.chain.invoke.return_value = """要重置笔记本到出厂设置，有两种方法：

方法一（软件重置）：
通过 Windows 设置进行系统重置，可以选择保留个人文件。

方法二（BIOS 重置）：
进入 BIOS 恢复出厂默认设置。"""
        
        query = "如何把笔记本恢复到出厂设置？"
        
        # 使用 rag_summarize 进行完整流程
        response = generator.rag_summarize(query)
        
        assert response is not None
        assert len(response) > 50  # 回答应该有一定长度
        assert "重置" in response or "恢复" in response
    
    def test_error_scenarios_handling(self, mock_rag_pipeline):
        """测试错误场景处理"""
        retriever = mock_rag_pipeline['retriever']
        generator = mock_rag_pipeline['generator']
        
        # 场景 1: 检索无结果
        retriever.retriever.invoke.return_value = []
        generator.chain.invoke.return_value = "抱歉，未找到相关信息"
        
        query = "非常冷门的问题"
        context_docs = retriever.retrieve(query)
        response = generator.generate(query, context_docs)
        
        assert response is not None
    
    def test_multiple_queries_batch(self, mock_rag_pipeline):
        """测试批量查询处理"""
        retriever = mock_rag_pipeline['retriever']
        generator = mock_rag_pipeline['generator']
        
        queries = [
            "笔记本无法开机",
            "系统运行缓慢",
            "如何清理风扇",
        ]
        
        responses = []
        
        for query in queries:
            retriever.retriever.invoke.return_value = [
                Document(page_content=f"关于{query}的解答", metadata={"source": "kb.pdf"})
            ]
            generator.chain.invoke.return_value = f"针对{query}的建议..."
            
            context_docs = retriever.retrieve(query)
            response = generator.generate(query, context_docs)
            responses.append(response)
        
        assert len(responses) == 3
        assert all(resp is not None for resp in responses)
    
    def test_metadata_preservation_through_pipeline(self, mock_rag_pipeline):
        """测试元数据在流程中的保留"""
        retriever = mock_rag_pipeline['retriever']
        
        original_docs = [
            Document(
                page_content="重要内容",
                metadata={
                    "source": "important.pdf",
                    "page": 10,
                    "chapter": "故障排除",
                    "confidence": 0.95
                }
            )
        ]
        
        retriever.retriever.invoke.return_value = original_docs
        
        results = retriever.retrieve("查询")
        
        assert len(results) == 1
        assert results[0].metadata["source"] == "important.pdf"
        assert results[0].metadata["page"] == 10
        assert results[0].metadata["chapter"] == "故障排除"
