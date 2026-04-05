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
        self.memory_service = None
    
    def execute_stream(self, messages: list):
        """
        流式执行
        :param messages: 完整的消息列表（包含历史对话和当前问题）
        """
        input_dict = {
            "messages": messages
        }
        
        # 调试输出：打印实际发送给 LLM 的消息
        print(f"\n=== 发送给 LLM 的消息 ===")
        for msg in messages:
            role = msg.get('role', 'unknown')
            content_preview = msg.get('content', '')[:200]
            print(f"[{role}]: {content_preview}...")
        print(f"=== 消息结束 ===\n")
        
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"
    
    def execute(self, messages: list) -> str:
        """
        同步执行
        :param messages: 完整的消息列表
        :return: 完整响应文本
        """
        response = ""
        for chunk in self.execute_stream(messages):
            response += chunk
        return response
