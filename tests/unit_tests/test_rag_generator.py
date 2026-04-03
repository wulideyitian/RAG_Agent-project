"""
RAG 生成器单元测试
测试 RAGGenerator 的各项功能
"""
import pytest
from unittest.mock import Mock, patch
from langchain_core.documents import Document


class TestRAGGenerator:
    """RAGGenerator 测试类"""
    
    @pytest.fixture
    def rag_generator(self):
        """初始化 RAG 生成器（完全 mock）"""
        with patch('core.rag.generator.ChatTongyi'):
            with patch('core.rag.generator.load_rag_prompts') as mock_load_prompts:
                with patch('core.rag.generator.StrOutputParser'):
                    with patch('core.rag.generator.PromptTemplate'):
                        mock_load_prompts.return_value = "测试提示词模板：{input} {context}"
                        
                        from core.rag.generator import RAGGenerator
                        
                        generator = RAGGenerator()
                        
                        # Mock chain
                        mock_chain = Mock()
                        generator.chain = mock_chain
                        
                        yield generator
    
    def test_init(self, rag_generator):
        """测试初始化"""
        assert rag_generator.prompt_text is not None
        assert rag_generator.prompt_template is not None
        assert rag_generator.model is not None
        assert rag_generator.chain is not None
    
    def test_generate_success(self, rag_generator):
        """测试成功生成回答"""
        context_docs = [
            Document(page_content="这是参考内容 1", metadata={"source": "doc1.pdf"}),
            Document(page_content="这是参考内容 2", metadata={"source": "doc2.pdf"}),
        ]
        
        rag_generator.chain.invoke.return_value = "这是生成的回答"
        
        query = "用户问题"
        response = rag_generator.generate(query, context_docs)
        
        assert response == "这是生成的回答"
        rag_generator.chain.invoke.assert_called_once()
    
    def test_generate_with_single_document(self, rag_generator):
        """测试单个文档生成"""
        context_docs = [
            Document(page_content="唯一参考文档", metadata={"source": "single.pdf"})
        ]
        
        rag_generator.chain.invoke.return_value = "基于唯一文档的回答"
        
        query = "问题"
        response = rag_generator.generate(query, context_docs)
        
        assert response == "基于唯一文档的回答"
    
    def test_generate_with_empty_documents(self, rag_generator):
        """测试空文档列表生成"""
        context_docs = []
        
        rag_generator.chain.invoke.return_value = "无参考内容的回答"
        
        query = "问题"
        response = rag_generator.generate(query, context_docs)
        
        assert response == "无参考内容的回答"
    
    def test_generate_error_handling(self, rag_generator):
        """测试生成异常处理"""
        context_docs = [Document(page_content="内容", metadata={})]
        rag_generator.chain.invoke.side_effect = Exception("生成失败")
        
        query = "问题"
        
        with pytest.raises(Exception) as exc_info:
            rag_generator.generate(query, context_docs)
        
        assert "RAG 生成失败" in str(exc_info.value)
    
    def test_format_context(self, rag_generator):
        """测试上下文格式化"""
        docs = [
            Document(
                page_content="第一段内容",
                metadata={"source": "source1.pdf"}
            ),
            Document(
                page_content="第二段内容",
                metadata={"source": "source2.pdf"}
            ),
        ]
        
        formatted = rag_generator._format_context(docs)
        
        assert "【参考资料 1】" in formatted
        assert "【参考资料 2】" in formatted
        assert "第一段内容" in formatted
        assert "第二段内容" in formatted
        assert "source1.pdf" in formatted
        assert "source2.pdf" in formatted
    
    def test_format_context_single_doc(self, rag_generator):
        """测试单个文档格式化"""
        docs = [
            Document(
                page_content="唯一内容",
                metadata={"source": "single.pdf"}
            )
        ]
        
        formatted = rag_generator._format_context(docs)
        
        assert "【参考资料 1】" in formatted
        assert "唯一内容" in formatted
    
    def test_format_context_unknown_source(self, rag_generator):
        """测试未知来源格式化"""
        docs = [
            Document(
                page_content="内容",
                metadata={}  # 没有 source
            )
        ]
        
        formatted = rag_generator._format_context(docs)
        
        assert "【参考资料 1】" in formatted
        assert "未知" in formatted
    
    def test_format_context_preserves_content(self, rag_generator):
        """测试格式化保留完整内容"""
        long_content = "这是一段很长的文本内容。" * 50
        docs = [
            Document(page_content=long_content, metadata={"source": "test.pdf"})
        ]
        
        formatted = rag_generator._format_context(docs)
        
        assert long_content in formatted
    
    def test_rag_summarize(self, rag_generator):
        """测试完整的 RAG 流程"""
        # RetrieverService 是在 rag_summarize 方法内部导入的，需要 patch 正确的路径
        with patch('core.rag.retriever.RetrieverService') as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.retrieve.return_value = [
                Document(page_content="检索到的内容", metadata={"source": "kb.pdf"})
            ]
            mock_retriever_class.return_value = mock_retriever
            
            rag_generator.chain.invoke.return_value = "最终回答"
            
            query = "笔记本无法开机怎么办？"
            response = rag_generator.rag_summarize(query)
            
            assert response == "最终回答"
            mock_retriever.retrieve.assert_called_once_with(query)
            rag_generator.chain.invoke.assert_called_once()
    
    def test_rag_summarize_no_results(self, rag_generator):
        """测试 RAG 流程无检索结果"""
        # RetrieverService 是在 rag_summarize 方法内部导入的，需要 patch 正确的路径
        with patch('core.rag.retriever.RetrieverService') as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.retrieve.return_value = []
            mock_retriever_class.return_value = mock_retriever
            
            rag_generator.chain.invoke.return_value = "未找到相关信息的回答"
            
            query = "冷门问题"
            response = rag_generator.rag_summarize(query)
            
            assert response == "未找到相关信息的回答"
    
    def test_generate_invokes_chain_with_correct_params(self, rag_generator):
        """测试链调用的参数正确性"""
        context_docs = [
            Document(page_content="参考内容", metadata={"source": "test.pdf"})
        ]
        
        rag_generator.chain.invoke.return_value = "回答"
        
        query = "测试问题"
        rag_generator.generate(query, context_docs)
        
        call_args = rag_generator.chain.invoke.call_args[0][0]
        assert call_args["input"] == query
        assert "context" in call_args
        assert "参考内容" in call_args["context"]
    
    def test_multiple_generate_calls(self, rag_generator):
        """测试多次生成调用"""
        context_docs = [Document(page_content="内容", metadata={})]
        rag_generator.chain.invoke.side_effect = ["回答 1", "回答 2", "回答 3"]
        
        queries = ["问题 1", "问题 2", "问题 3"]
        responses = []
        
        for i, query in enumerate(queries):
            response = rag_generator.generate(query, context_docs)
            responses.append(response)
        
        assert len(responses) == 3
        assert responses == ["回答 1", "回答 2", "回答 3"]
    
    def test_generate_with_complex_query(self, rag_generator):
        """测试复杂查询生成"""
        context_docs = [
            Document(
                page_content="Windows 11 系统重置步骤...",
                metadata={"source": "system_guide.pdf"}
            ),
            Document(
                page_content="BIOS 设置恢复出厂配置...",
                metadata={"source": "hardware_manual.pdf"}
            ),
        ]
        
        rag_generator.chain.invoke.return_value = "详细的重置步骤说明..."
        
        query = "如何重置笔记本电脑到出厂设置？需要保留数据。"
        response = rag_generator.generate(query, context_docs)
        
        assert response == "详细的重置步骤说明..."
