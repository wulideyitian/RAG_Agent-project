"""
Agent 内存管理单元测试
测试 SessionMemory 的各项功能
"""
import pytest
from core.agent.memory import SessionMemory


class TestSessionMemory:
    """SessionMemory 测试类"""
    
    @pytest.fixture
    def memory(self):
        """初始化记忆管理器"""
        return SessionMemory()
    
    def test_init(self, memory):
        """测试初始化"""
        mem = memory.get_memory()
        assert mem["mentioned_models"] == []
        assert mem["budget"] is None
        assert mem["usage_scenario"] is None
        assert mem["location"] is None
        assert mem["preferences"] == {}
    
    def test_add_mentioned_model_single(self, memory):
        """测试添加单个笔记本型号"""
        memory.add_mentioned_model("联想 ThinkPad X1")
        mem = memory.get_memory()
        assert "联想 ThinkPad X1" in mem["mentioned_models"]
        assert len(mem["mentioned_models"]) == 1
    
    def test_add_mentioned_model_multiple(self, memory):
        """测试添加多个笔记本型号"""
        memory.add_mentioned_model("联想 ThinkPad X1")
        memory.add_mentioned_model("戴尔 XPS 13")
        memory.add_mentioned_model("惠普战 66")
        
        mem = memory.get_memory()
        assert len(mem["mentioned_models"]) == 3
        assert "联想 ThinkPad X1" in mem["mentioned_models"]
        assert "戴尔 XPS 13" in mem["mentioned_models"]
        assert "惠普战 66" in mem["mentioned_models"]
    
    def test_add_mentioned_model_duplicate(self, memory):
        """测试添加重复的笔记本型号"""
        memory.add_mentioned_model("联想 ThinkPad X1")
        memory.add_mentioned_model("联想 ThinkPad X1")
        memory.add_mentioned_model("联想 ThinkPad X1")
        
        mem = memory.get_memory()
        assert len(mem["mentioned_models"]) == 1
        assert mem["mentioned_models"][0] == "联想 ThinkPad X1"
    
    def test_add_mentioned_model_empty(self, memory):
        """测试添加空字符串型号"""
        memory.add_mentioned_model("")
        memory.add_mentioned_model(None)
        
        mem = memory.get_memory()
        # 空字符串和 None 不应该被添加
        assert "" not in mem["mentioned_models"]
    
    def test_set_budget(self, memory):
        """测试设置预算"""
        memory.set_budget("5000-8000 元")
        mem = memory.get_memory()
        assert mem["budget"] == "5000-8000 元"
    
    def test_set_budget_update(self, memory):
        """测试更新预算"""
        memory.set_budget("5000 元")
        memory.set_budget("8000 元")
        
        mem = memory.get_memory()
        assert mem["budget"] == "8000 元"
    
    def test_set_usage_scenario(self, memory):
        """测试设置用途场景"""
        memory.set_usage_scenario("办公")
        mem = memory.get_memory()
        assert mem["usage_scenario"] == "办公"
    
    def test_set_usage_scenario_multiple(self, memory):
        """测试多次设置用途场景"""
        scenarios = ["办公", "游戏", "设计", "编程"]
        for scenario in scenarios:
            memory.set_usage_scenario(scenario)
        
        mem = memory.get_memory()
        assert mem["usage_scenario"] == "编程"
    
    def test_set_location(self, memory):
        """测试设置地理位置"""
        memory.set_location("北京")
        mem = memory.get_memory()
        assert mem["location"] == "北京"
    
    def test_set_location_update(self, memory):
        """测试更新地理位置"""
        memory.set_location("上海")
        memory.set_location("深圳")
        
        mem = memory.get_memory()
        assert mem["location"] == "深圳"
    
    def test_add_preference_single(self, memory):
        """测试添加单个偏好"""
        memory.add_preference("品牌", "联想")
        mem = memory.get_memory()
        assert mem["preferences"]["品牌"] == "联想"
    
    def test_add_preference_multiple(self, memory):
        """测试添加多个偏好"""
        memory.add_preference("品牌", "联想")
        memory.add_preference("屏幕尺寸", "14 英寸")
        memory.add_preference("重量", "轻薄")
        
        mem = memory.get_memory()
        assert len(mem["preferences"]) == 3
        assert mem["preferences"]["品牌"] == "联想"
        assert mem["preferences"]["屏幕尺寸"] == "14 英寸"
        assert mem["preferences"]["重量"] == "轻薄"
    
    def test_add_preference_update(self, memory):
        """测试更新偏好"""
        memory.add_preference("品牌", "联想")
        memory.add_preference("品牌", "戴尔")
        
        mem = memory.get_memory()
        assert mem["preferences"]["品牌"] == "戴尔"
    
    def test_get_memory_returns_copy(self, memory):
        """测试获取记忆返回的是副本"""
        memory.add_mentioned_model("联想 ThinkPad X1")
        
        mem1 = memory.get_memory()
        mem1["mentioned_models"].append("惠普战 66")
        
        mem2 = memory.get_memory()
        assert len(mem2["mentioned_models"]) == 1
        assert "惠普战 66" not in mem2["mentioned_models"]
    
    def test_to_json(self, memory):
        """测试转为 JSON 字符串"""
        memory.add_mentioned_model("联想 ThinkPad X1")
        memory.set_budget("8000 元")
        memory.add_preference("品牌", "联想")
        
        json_str = memory.to_json()
        
        assert isinstance(json_str, str)
        assert "联想 ThinkPad X1" in json_str
        assert "8000 元" in json_str
        assert "联想" in json_str
    
    def test_to_json_with_chinese(self, memory):
        """测试 JSON 包含中文"""
        memory.set_usage_scenario("商务办公")
        
        json_str = memory.to_json()
        assert "商务办公" in json_str
    
    def test_clear(self, memory):
        """测试清空记忆"""
        memory.add_mentioned_model("联想 ThinkPad X1")
        memory.set_budget("8000 元")
        memory.set_usage_scenario("办公")
        memory.set_location("北京")
        memory.add_preference("品牌", "联想")
        
        memory.clear()
        
        mem = memory.get_memory()
        assert mem["mentioned_models"] == []
        assert mem["budget"] is None
        assert mem["usage_scenario"] is None
        assert mem["location"] is None
        assert mem["preferences"] == {}
    
    def test_clear_twice(self, memory):
        """测试多次清空"""
        memory.clear()
        memory.clear()
        
        mem = memory.get_memory()
        assert mem["mentioned_models"] == []
        assert mem["budget"] is None
    
    def test_memory_workflow(self, memory):
        """测试完整的记忆工作流程"""
        # 用户提到多款笔记本
        memory.add_mentioned_model("联想 ThinkPad X1")
        memory.add_mentioned_model("戴尔 XPS 13")
        
        # 用户设置预算
        memory.set_budget("10000-15000 元")
        
        # 用户说明用途
        memory.set_usage_scenario("商务出差")
        
        # 用户位置
        memory.set_location("北京")
        
        # 用户偏好
        memory.add_preference("品牌", "联想")
        memory.add_preference("重量", "轻薄")
        memory.add_preference("续航", "长续航")
        
        # 验证所有信息
        mem = memory.get_memory()
        assert len(mem["mentioned_models"]) == 2
        assert mem["budget"] == "10000-15000 元"
        assert mem["usage_scenario"] == "商务出差"
        assert mem["location"] == "北京"
        assert len(mem["preferences"]) == 3
        
        # 转为 JSON
        json_str = memory.to_json()
        assert "商务出差" in json_str
        
        # 清空记忆
        memory.clear()
        mem_after_clear = memory.get_memory()
        assert mem_after_clear["mentioned_models"] == []
