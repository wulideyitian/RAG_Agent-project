"""
Agent 对话业务服务
封装 Agent 对话的核心业务逻辑
支持对话记录的批量保存（可选）
"""
from typing import Generator, Optional
from core.agent.react_agent import ReactAgent
from core.agent.context_manager import ContextManager
from app.utils.config_handler import agent_conf
import os


class AgentService:
    """
    Agent 对话服务
    提供流式和非流式的问答接口
    支持长期记忆存储和检索
    """
    
    def __init__(self):
        # 检查必要的环境变量
        self._check_env()
        self.agent = ReactAgent()
        
        # 初始化上下文管理器
        context_config = agent_conf.get("context_config", {})
        self.context_manager = ContextManager(
            max_tokens=context_config.get("max_tokens", 6000),
            window_size=context_config.get("window_size", 10),
            min_keep_turns=context_config.get("min_keep_turns", 5),
            strategy=context_config.get("strategy", "hybrid"),
            model_encoding=context_config.get("model_encoding", "cl100k_base"),
        )
    

    def _check_env(self):
        """检查必要的环境变量是否配置"""
        required_vars = ['DASHSCOPE_API_KEY']
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            raise RuntimeError(
                f"缺少必要的环境变量：{', '.join(missing)}\n"
                f"请设置环境变量后再使用 Agent 服务"
            )
    
    def execute_stream(
        self, 
        messages: list,
    ) -> Generator[str, None, None]:
        """
        执行流式问答
        :param messages: 完整的消息列表（包含历史对话和当前问题）
        :return: 流式响应生成器
        """
        # 优化上下文
        optimized_messages, stats = self.context_manager.optimize_context(messages)
        
        # 执行 Agent 并收集响应
        response_chunks = []
        for chunk in self.agent.execute_stream(optimized_messages):
            response_chunks.append(chunk)
            yield chunk
    
    def execute(
        self, 
        messages: list,
    ) -> str:
        """
        执行同步问答（非流式）
        :param messages: 完整的消息列表
        :return: 完整响应文本
        """
        # 优化上下文
        optimized_messages, stats = self.context_manager.optimize_context(messages)
        
        response = ""
        for chunk in self.execute_stream(optimized_messages):
            response += chunk
        return response
