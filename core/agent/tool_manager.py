"""
工具管理器
管理所有 Agent 工具的注册和调用
"""
from agent.tools.agent_tools import (
    rag_summarize, get_weather, get_user_location, get_user_id,
    get_current_month, fetch_external_data, fill_context_for_report,
    get_user_device_info, laptop_spec_tool, model_compare_tool,
    fault_diagnose_tool, purchase_recommend_tool, memory_tool,
    performance_calc_tool, structured_output_tool
)


class ToolManager:
    """工具管理器"""
    
    def __init__(self):
        self.tools = {
            "rag_summarize": rag_summarize,
            "get_weather": get_weather,
            "get_user_location": get_user_location,
            "get_user_id": get_user_id,
            "get_current_month": get_current_month,
            "fetch_external_data": fetch_external_data,
            "fill_context_for_report": fill_context_for_report,
            "get_user_device_info": get_user_device_info,
            "laptop_spec_tool": laptop_spec_tool,
            "model_compare_tool": model_compare_tool,
            "fault_diagnose_tool": fault_diagnose_tool,
            "purchase_recommend_tool": purchase_recommend_tool,
            "memory_tool": memory_tool,
            "performance_calc_tool": performance_calc_tool,
            "structured_output_tool": structured_output_tool,
        }
    
    def get_all_tools(self):
        """获取所有工具列表"""
        return list(self.tools.values())
    
    def get_tool_by_name(self, name: str):
        """根据名称获取工具"""
        return self.tools.get(name)
    
    def register_tool(self, name: str, tool_func):
        """注册新工具"""
        self.tools[name] = tool_func
    
    def unregister_tool(self, name: str):
        """注销工具"""
        if name in self.tools:
            del self.tools[name]
