"""
Agent 对话业务服务
封装 Agent 对话的核心业务逻辑
"""
from typing import Generator
from core.agent.react_agent import ReactAgent
import os


class AgentService:
    """
    Agent 对话服务
    提供流式和非流式的问答接口
    """
    
    def __init__(self):
        # 检查必要的环境变量
        self._check_env()
        self.agent = ReactAgent()
    
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
    
    def execute_stream(self, query: str) -> Generator[str, None, None]:
        """
        执行流式问答
        :param query: 用户提问
        :return: 流式响应生成器
        """
        yield from self.agent.execute_stream(query)
    
    def execute(self, query: str) -> str:
        """
        执行同步问答（非流式）
        :param query: 用户提问
        :return: 完整响应文本
        """
        response = ""
        for chunk in self.agent.execute_stream(query):
            response += chunk
        return response
