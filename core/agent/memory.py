"""
会话记忆管理
管理多轮对话的上下文信息
"""
import json
from typing import Dict, List


class SessionMemory:
    """会话记忆管理器"""
    
    def __init__(self):
        self.memory: Dict = {
            "mentioned_models": [],
            "budget": None,
            "usage_scenario": None,
            "location": None,
            "preferences": {}
        }
    
    def add_mentioned_model(self, model_name: str):
        """添加提到的笔记本型号"""
        if model_name and model_name not in self.memory["mentioned_models"]:
            self.memory["mentioned_models"].append(model_name)
    
    def set_budget(self, budget: str):
        """设置预算"""
        self.memory["budget"] = budget
    
    def set_usage_scenario(self, scenario: str):
        """设置用途场景"""
        self.memory["usage_scenario"] = scenario
    
    def set_location(self, location: str):
        """设置地理位置"""
        self.memory["location"] = location
    
    def add_preference(self, key: str, value):
        """添加偏好"""
        self.memory["preferences"][key] = value
    
    def get_memory(self) -> Dict:
        """获取完整记忆"""
        return self.memory.copy()
    
    def to_json(self) -> str:
        """转为 JSON 字符串"""
        return json.dumps(self.memory, ensure_ascii=False, indent=2)
    
    def clear(self):
        """清空记忆"""
        self.memory = {
            "mentioned_models": [],
            "budget": None,
            "usage_scenario": None,
            "location": None,
            "preferences": {}
        }
