"""
测试工具模块
提供通用的测试辅助函数和 fixtures
"""
import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent.parent / "test_data"


@pytest.fixture
def temp_file():
    """创建临时文件（自动清理）"""
    fd, path = tempfile.mkstemp()
    try:
        yield path
    finally:
        os.close(fd)
        if os.path.exists(path):
            os.unlink(path)


@pytest.fixture
def temp_dir():
    """创建临时目录（自动清理）"""
    dirpath = tempfile.mkdtemp()
    try:
        yield Path(dirpath)
    finally:
        import shutil
        shutil.rmtree(dirpath, ignore_errors=True)


@pytest.fixture
def sample_text():
    """示例文本"""
    return """笔记本计算机是一种便携式计算设备，通常具有以下特点：

1. 集成设计：将显示器、键盘、触控板、主板、硬盘等组件集成在一个紧凑的机身中。

2. 便携性：重量轻，体积小，适合随身携带。

3. 电池供电：内置可充电电池，可在不接电源的情况下使用数小时。

4. 无线网络：支持 Wi-Fi 和蓝牙连接，方便网络访问和外设连接。

5. 性能强大：现代笔记本电脑配备高性能处理器、大容量内存和固态硬盘，能够满足各种办公、娱乐和专业应用需求。

选购笔记本时需要考虑用途、预算、品牌、售后服务等因素。"""


@pytest.fixture
def sample_documents(sample_text):
    """示例文档列表"""
    from langchain_core.documents import Document
    
    return [
        Document(
            page_content=sample_text,
            metadata={"source": "laptop_guide.txt", "file_type": "txt"}
        ),
        Document(
            page_content="故障排除指南：如果笔记本无法开机，请检查电源适配器、电池连接和电源插座。",
            metadata={"source": "troubleshooting.pdf", "file_type": "pdf"}
        ),
        Document(
            page_content="系统维护建议：定期清理系统垃圾文件，更新驱动程序，保持系统流畅运行。",
            metadata={"source": "maintenance.md", "file_type": "md"}
        )
    ]


@pytest.fixture
def mock_embedding_vectors():
    """Mock 嵌入向量"""
    return {
        "文本一": [0.1, 0.2, 0.3, 0.4, 0.5],
        "文本二": [0.2, 0.3, 0.4, 0.5, 0.6],
        "查询": [0.15, 0.25, 0.35, 0.45, 0.55],
    }


@pytest.fixture
def mock_similarity_scores():
    """Mock 相似度分数"""
    return [0.95, 0.87, 0.76, 0.65, 0.54]


def create_test_file(directory: Path, filename: str, content: str, encoding: str = "utf-8"):
    """创建测试文件"""
    filepath = directory / filename
    filepath.write_text(content, encoding=encoding)
    return filepath


def assert_document_structure(doc, expected_keys=None):
    """断言文档结构"""
    from langchain_core.documents import Document
    
    assert isinstance(doc, Document), "应该是 Document 类型"
    assert hasattr(doc, 'page_content'), "应该包含 page_content"
    assert hasattr(doc, 'metadata'), "应该包含 metadata"
    
    if expected_keys:
        for key in expected_keys:
            assert key in doc.metadata, f"metadata 应该包含 {key}"


def assert_vector_structure(vector, expected_dimension=None):
    """断言向量结构"""
    assert isinstance(vector, list), "向量应该是列表"
    assert len(vector) > 0, "向量不应该为空"
    
    if expected_dimension:
        assert len(vector) == expected_dimension, f"向量维度应该是 {expected_dimension}"
    
    assert all(isinstance(v, (int, float)) for v in vector), "向量元素都应该是数值"
