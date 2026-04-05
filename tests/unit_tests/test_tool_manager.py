"""
工具管理器单元测试
测试 ToolManager 的各项功能
"""
import pytest
from core.agent.tool_manager import ToolManager
from langchain_core.tools import BaseTool


class TestToolManager:
    """ToolManager 测试类"""
    
    @pytest.fixture
    def tool_manager(self):
        """初始化工具管理器"""
        return ToolManager()
    
    def test_init(self, tool_manager):
        """测试初始化"""
        assert tool_manager.tools is not None
        assert len(tool_manager.tools) > 0
    
    def test_get_all_tools(self, tool_manager):
        """测试获取所有工具列表"""
        tools = tool_manager.get_all_tools()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
    
    def test_get_all_tools_count(self, tool_manager):
        """测试工具数量"""
        tools = tool_manager.get_all_tools()
        
        # 验证默认注册的工具数量
        expected_tools = [
            "rag_summarize", "get_user_device_info",
            "laptop_spec_tool", "model_compare_tool",
            "fault_diagnose_tool", "purchase_recommend_tool",
            "performance_calc_tool"
        ]
        
        assert len(tools) == len(expected_tools)
    
    def test_get_tool_by_name_existing(self, tool_manager):
        """测试获取存在的工具"""
        tool = tool_manager.get_tool_by_name("rag_summarize")
        
        assert tool is not None
        # 验证是 BaseTool 的实例（StructuredTool 继承自 BaseTool）
        assert isinstance(tool, BaseTool)
    
    def test_get_tool_by_name_multiple(self, tool_manager):
        """测试获取多个工具"""
        tool_names = [
            "rag_summarize", "laptop_spec_tool", 
            "fault_diagnose_tool", "purchase_recommend_tool"
        ]
        
        for name in tool_names:
            tool = tool_manager.get_tool_by_name(name)
            assert tool is not None
            assert isinstance(tool, BaseTool)
    
    def test_get_tool_by_name_not_exist(self, tool_manager):
        """测试获取不存在的工具"""
        tool = tool_manager.get_tool_by_name("non_existent_tool")
        
        assert tool is None
    
    def test_get_tool_by_name_case_sensitive(self, tool_manager):
        """测试工具名称大小写敏感"""
        tool1 = tool_manager.get_tool_by_name("rag_summarize")
        tool2 = tool_manager.get_tool_by_name("Rag_Summarize")
        
        assert tool1 is not None
        assert tool2 is None
    
    def test_register_tool(self, tool_manager):
        """测试注册新工具"""
        def mock_tool():
            return "mock tool result"
        
        tool_manager.register_tool("mock_tool", mock_tool)
        
        tool = tool_manager.get_tool_by_name("mock_tool")
        assert tool is not None
        assert tool == mock_tool
        
        all_tools = tool_manager.get_all_tools()
        assert len(all_tools) > 0
    
    def test_register_tool_overwrite(self, tool_manager):
        """测试覆盖已有工具"""
        def original_tool():
            return "original"
        
        def new_tool():
            return "new"
        
        tool_manager.register_tool("test_tool", original_tool)
        tool_manager.register_tool("test_tool", new_tool)
        
        tool = tool_manager.get_tool_by_name("test_tool")
        assert tool == new_tool
        assert tool != original_tool
    
    def test_unregister_tool(self, tool_manager):
        """测试注销工具"""
        def temp_tool():
            return "temp"
        
        tool_manager.register_tool("temp_tool", temp_tool)
        
        # 确认工具存在
        assert tool_manager.get_tool_by_name("temp_tool") is not None
        
        # 注销工具
        tool_manager.unregister_tool("temp_tool")
        
        # 确认工具已删除
        assert tool_manager.get_tool_by_name("temp_tool") is None
    
    def test_unregister_tool_nonexistent(self, tool_manager):
        """测试注销不存在的工具"""
        # 不应该抛出异常
        tool_manager.unregister_tool("non_existent_tool")
        
        # 工具列表应该不变
        tools_before = tool_manager.get_all_tools()
        tool_manager.unregister_tool("another_fake")
        tools_after = tool_manager.get_all_tools()
        
        assert len(tools_before) == len(tools_after)
    
    def test_unregister_and_reregister(self, tool_manager):
        """测试注销后重新注册"""
        def tool_v1():
            return "version 1"
        
        def tool_v2():
            return "version 2"
        
        tool_manager.register_tool("my_tool", tool_v1)
        tool_manager.unregister_tool("my_tool")
        tool_manager.register_tool("my_tool", tool_v2)
        
        tool = tool_manager.get_tool_by_name("my_tool")
        assert tool == tool_v2
        assert tool != tool_v1
    
    def test_tool_manager_state_isolation(self, tool_manager):
        """测试工具管理器状态隔离"""
        tool_manager.register_tool("tool_a", lambda: "a")
        tool_manager.register_tool("tool_b", lambda: "b")
        
        tools = tool_manager.get_all_tools()
        tool_names = list(tool_manager.tools.keys())
        
        assert "tool_a" in tool_names
        assert "tool_b" in tool_names
    
    def test_get_tool_workflow(self, tool_manager):
        """测试获取工具的完整流程"""
        # 检查默认工具
        default_tool = tool_manager.get_tool_by_name("rag_summarize")
        assert default_tool is not None
        
        # 注册新工具
        def custom_tool(param):
            return f"custom: {param}"
        
        tool_manager.register_tool("custom_tool", custom_tool)
        
        # 获取并使用工具
        retrieved_tool = tool_manager.get_tool_by_name("custom_tool")
        assert retrieved_tool is not None
        
        result = retrieved_tool("test param")
        assert result == "custom: test param"
        
        # 注销工具
        tool_manager.unregister_tool("custom_tool")
        assert tool_manager.get_tool_by_name("custom_tool") is None
    
    def test_multiple_tool_operations(self, tool_manager):
        """测试多次工具操作"""
        operations_log = []
        
        # 注册多个工具
        for i in range(5):
            tool_name = f"tool_{i}"
            tool_manager.register_tool(tool_name, lambda x=i: x)
            operations_log.append(f"registered_{tool_name}")
        
        # 验证所有工具都存在
        for i in range(5):
            tool = tool_manager.get_tool_by_name(f"tool_{i}")
            assert tool is not None
        
        # 删除部分工具
        for i in range(0, 5, 2):
            tool_manager.unregister_tool(f"tool_{i}")
            operations_log.append(f"unregistered_tool_{i}")
        
        # 验证删除结果
        assert tool_manager.get_tool_by_name("tool_0") is None
        assert tool_manager.get_tool_by_name("tool_1") is not None
        assert tool_manager.get_tool_by_name("tool_2") is None
        assert tool_manager.get_tool_by_name("tool_3") is not None
        assert tool_manager.get_tool_by_name("tool_4") is None
