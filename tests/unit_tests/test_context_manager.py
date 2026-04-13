"""
上下文管理器单元测试
测试 Token 计数、窗口管理和智能裁剪功能
"""
import pytest
from core.agent.context_manager import ContextManager


class TestContextManager:
    """上下文管理器测试类"""
    
    @pytest.fixture
    def context_manager(self):
        """创建默认的上下文管理器实例"""
        return ContextManager(
            max_tokens=6000,
            window_size=10,
            min_keep_turns=5,
            strategy="hybrid"
        )
    
    @pytest.fixture
    def sample_messages(self):
        """创建示例消息列表(20轮对话)"""
        messages = []
        for i in range(20):
            messages.append({"role": "user", "content": f"用户问题 {i+1}"})
            messages.append({"role": "assistant", "content": f"助手回答 {i+1}"})
        return messages
    
    # ========== Token 计数测试 ==========
    
    def test_count_tokens_empty(self, context_manager):
        """测试空文本 token 计数"""
        assert context_manager.count_tokens("") == 0
    
    def test_count_tokens_simple(self, context_manager):
        """测试简单文本 token 计数"""
        tokens = context_manager.count_tokens("Hello world")
        assert tokens > 0
    
    def test_count_tokens_chinese(self, context_manager):
        """测试中文文本 token 计数"""
        tokens = context_manager.count_tokens("你好世界")
        assert tokens > 0
    
    def test_count_message_tokens(self, context_manager):
        """测试单条消息 token 计数"""
        msg = {"role": "user", "content": "测试消息"}
        tokens = context_manager.count_message_tokens(msg)
        assert tokens > 0
    
    def test_count_messages_tokens(self, context_manager, sample_messages):
        """测试消息列表 token 计数"""
        tokens = context_manager.count_messages_tokens(sample_messages)
        assert tokens > 0
    
    # ========== 混合策略测试 ==========
    
    def test_hybrid_strategy_no_optimization_needed(self, context_manager):
        """测试不需要优化的情况(消息较少)"""
        messages = [
            {"role": "user", "content": "问题1"},
            {"role": "assistant", "content": "回答1"},
        ]
        optimized, stats = context_manager.optimize_context(messages)
        
        assert len(optimized) == len(messages)
        assert stats["removed_count"] == 0
    
    def test_hybrid_strategy_respects_min_keep_turns(self, context_manager):
        """测试最小保留轮数保证"""
        # 创建大量消息
        messages = []
        for i in range(30):
            messages.append({"role": "user", "content": f"问题 {i}" * 10})
            messages.append({"role": "assistant", "content": f"回答 {i}" * 10})
        
        optimized, stats = context_manager.optimize_context(messages)
        
        # 至少保留 min_keep_turns 轮
        assert len(optimized) >= context_manager.min_keep_turns * 2
    
    def test_hybrid_strategy_token_limit(self, context_manager):
        """测试 token 限制"""
        # 创建超长消息,确保总 token 数远超限制
        messages = []
        for i in range(20):
            # 每条消息约 500 tokens,20 轮 = 40 条消息 ≈ 20000 tokens
            long_content = "这是一个很长的测试内容 " * 200
            messages.append({"role": "user", "content": long_content})
            messages.append({"role": "assistant", "content": long_content})
        
        optimized, stats = context_manager.optimize_context(messages)
        
        # 优化后的 token 数应该不超过限制(允许少量误差)
        # 但由于 min_keep_turns=5,至少会保留 10 条消息(约 5000 tokens)
        assert stats["optimized_tokens"] <= context_manager.max_tokens * 1.5
    
    def test_hybrid_strategy_prefers_recent(self, context_manager):
        """测试优先保留最近的消息"""
        messages = []
        for i in range(20):
            messages.append({"role": "user", "content": f"问题 {i+1}"})
            messages.append({"role": "assistant", "content": f"回答 {i+1}"})
        
        optimized, stats = context_manager.optimize_context(messages)
        
        # 检查最后一条消息是否被保留
        if optimized:
            assert optimized[-1]["content"] == "回答 20"
    
    # ========== Token 预算策略测试 ==========
    
    def test_token_budget_strategy(self):
        """测试纯 token 预算策略"""
        cm = ContextManager(strategy="token_budget", max_tokens=1000)
        
        messages = []
        for i in range(20):
            long_content = "测试内容 " * 50
            messages.append({"role": "user", "content": long_content})
            messages.append({"role": "assistant", "content": long_content})
        
        optimized, stats = cm.optimize_context(messages)
        
        assert stats["optimized_tokens"] <= cm.max_tokens * 1.1
    
    # ========== 滑动窗口策略测试 ==========
    
    def test_window_size_strategy(self):
        """测试滑动窗口策略"""
        cm = ContextManager(strategy="window_size", window_size=5)
        
        messages = []
        for i in range(20):
            messages.append({"role": "user", "content": f"问题 {i+1}"})
            messages.append({"role": "assistant", "content": f"回答 {i+1}"})
        
        optimized, stats = cm.optimize_context(messages)
        
        # 应该保留最后 5 轮 = 10 条消息
        assert len(optimized) == 10
    
    # ========== 系统提示测试 ==========
    
    def test_system_prompt_preserved(self, context_manager):
        """测试系统提示始终保留"""
        messages = [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "问题1"},
            {"role": "assistant", "content": "回答1"},
        ]
        
        system_prompt = "系统提示内容"
        optimized, stats = context_manager.optimize_context(
            messages, 
            system_prompt=system_prompt
        )
        
        # 检查系统提示是否在开头
        assert optimized[0]["role"] == "system"
        assert optimized[0]["content"] == system_prompt
    
    # ========== 边界情况测试 ==========
    
    def test_empty_messages(self, context_manager):
        """测试空消息列表"""
        optimized, stats = context_manager.optimize_context([])
        
        assert optimized == []
        assert stats["original_tokens"] == 0
    
    def test_single_message(self, context_manager):
        """测试单条消息"""
        messages = [{"role": "user", "content": "单个问题"}]
        optimized, stats = context_manager.optimize_context(messages)
        
        assert len(optimized) == 1
    
    def test_stats_accuracy(self, context_manager, sample_messages):
        """测试统计信息准确性"""
        optimized, stats = context_manager.optimize_context(sample_messages)
        
        assert stats["original_count"] == len(sample_messages)
        assert stats["optimized_count"] == len(optimized)
        assert stats["removed_count"] == stats["original_count"] - stats["optimized_count"]
        assert stats["saved_tokens"] == stats["original_tokens"] - stats["optimized_tokens"]
    
    # ========== 上下文统计测试 ==========
    
    def test_get_context_stats(self, context_manager, sample_messages):
        """测试获取上下文统计信息"""
        stats = context_manager.get_context_stats(sample_messages)
        
        assert stats["total_messages"] == len(sample_messages)
        assert stats["total_tokens"] > 0
        assert "user" in stats["role_breakdown"]
        assert "assistant" in stats["role_breakdown"]
        assert 0 <= stats["usage_percentage"] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
