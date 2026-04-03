"""
统一配置加载模块
复用 utils/config_handler.py 逻辑，提供统一的配置访问接口
"""
from app.utils.config_handler import (
    rag_conf,
    chroma_conf,
    prompts_conf,
    agent_conf,
    load_rag_config,
    load_chroma_config,
    load_prompts_config,
    load_agent_config,
)

__all__ = [
    "rag_conf",
    "chroma_conf",
    "prompts_conf",
    "agent_conf",
    "load_rag_config",
    "load_chroma_config",
    "load_prompts_config",
    "load_agent_config",
]
