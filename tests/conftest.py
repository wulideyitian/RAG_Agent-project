"""
pytest 配置文件
定义全局 fixtures 和配置
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 添加 tests 目录到 Python 路径
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))


@pytest.fixture(scope="session")
def project_root_path():
    """项目根目录路径"""
    return project_root


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """自动设置测试环境（每个测试都会运行）"""
    # 可以在这里设置环境变量、配置等
    original_cwd = Path.cwd()
    
    yield
    
    # 清理工作（如果需要）


@pytest.fixture
def enable_logging():
    """启用日志记录（用于调试）"""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    yield
    logging.shutdown()


# 导入通用测试工具（使用绝对路径）
from tests.utils.test_helpers import (
    temp_file,
    temp_dir,
    sample_text,
    sample_documents,
    mock_embedding_vectors,
    mock_similarity_scores,
    create_test_file,
    assert_document_structure,
    assert_vector_structure,
)
