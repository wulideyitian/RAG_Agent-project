"""
ReAct Agent 智能决策模块
负责意图识别、工具调用和对话管理
"""
from langchain.agents import create_agent
from core.embedding.embed_model import EmbedModelService
from langchain_community.chat_models.tongyi import ChatTongyi
from app.utils.config_handler import rag_conf

# 初始化聊天模型
chat_model = ChatTongyi(model=rag_conf["chat_model_name"])
from app.utils.prompt_loader import load_system_prompts
from core.agent.tool_manager import ToolManager
from core.agent.middleware import agent_middleware, log_before_agent_call, switch_prompt


class ReactAgent:
    """ReAct Agent"""
    
    def __init__(self):
        tool_manager = ToolManager()
        
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=tool_manager.get_all_tools(),
            middleware=[agent_middleware, log_before_agent_call, switch_prompt],
        )
    
    def execute_stream(self, query: str):
        """流式执行"""
        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }
        
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"
    
    def execute(self, query: str) -> str:
        """同步执行"""
        response = ""
        for chunk in self.execute_stream(query):
            response += chunk
        return response
