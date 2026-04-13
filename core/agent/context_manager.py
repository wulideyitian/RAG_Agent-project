"""
上下文管理器
负责 Token 计数、上下文窗口管理和智能裁剪
"""
import tiktoken
from typing import List, Dict, Tuple, Optional
from app.utils.logger_handler import logger


class ContextManager:
    """
    上下文管理器
    
    功能:
    1. Token 精确计数
    2. 滑动窗口管理
    3. 基于 Token 预算的智能裁剪
    4. 混合策略支持
    """
    
    def __init__(
        self,
        max_tokens: int = 6000,
        window_size: int = 10,
        min_keep_turns: int = 5,
        strategy: str = "hybrid",
        model_encoding: str = "cl100k_base",
    ):
        """
        初始化上下文管理器
        
        Args:
            max_tokens: 最大 token 限制
            window_size: 滑动窗口大小(轮数)
            min_keep_turns: 最少保留轮数
            strategy: 策略类型 (token_budget | window_size | hybrid)
            model_encoding: tiktoken encoding 名称
        """
        self.max_tokens = max_tokens
        self.window_size = window_size
        self.min_keep_turns = min_keep_turns
        self.strategy = strategy
        
        # 初始化 tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding(model_encoding)
        except Exception as e:
            logger.warning(f"无法加载 encoding {model_encoding}, 使用 cl100k_base: {e}")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        logger.info(
            f"ContextManager 初始化完成 | "
            f"max_tokens={max_tokens}, window_size={window_size}, "
            f"min_keep_turns={min_keep_turns}, strategy={strategy}"
        )
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本的 token 数量
        
        Args:
            text: 输入文本
            
        Returns:
            token 数量
        """
        if not text:
            return 0
        return len(self.tokenizer.encode(text))
    
    def count_message_tokens(self, message: Dict) -> int:
        """
        计算单条消息的 token 数量
        
        Args:
            message: 消息字典 {"role": "...", "content": "..."}
            
        Returns:
            token 数量
        """
        role = message.get("role", "")
        content = message.get("content", "")
        
        # 基础开销: role + 格式标记
        base_tokens = self.count_tokens(role) + 4
        
        # 内容 token
        content_tokens = self.count_tokens(content)
        
        return base_tokens + content_tokens
    
    def count_messages_tokens(self, messages: List[Dict]) -> int:
        """
        计算消息列表的总 token 数量
        
        Args:
            messages: 消息列表
            
        Returns:
            总 token 数量
        """
        total = 0
        for msg in messages:
            total += self.count_message_tokens(msg)
        return total
    
    def optimize_context(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
    ) -> Tuple[List[Dict], Dict]:
        """
        优化上下文
        
        Args:
            messages: 原始消息列表
            system_prompt: 系统提示(可选,始终保留)
            
        Returns:
            (优化后的消息列表, 统计信息字典)
        """
        if not messages:
            return [], {"original_tokens": 0, "optimized_tokens": 0, "removed_count": 0}
        
        # 分离系统提示和普通消息
        system_messages = []
        normal_messages = []
        
        for msg in messages:
            role = msg.get("role", "")
            if role == "system" and system_prompt is not None:
                # 如果有显式的 system_prompt 参数,跳过消息中的 system
                continue
            normal_messages.append(msg)
        
        # 添加系统提示到开头
        if system_prompt:
            system_messages = [{"role": "system", "content": system_prompt}]
        
        original_token_count = self.count_messages_tokens(normal_messages)
        
        # 根据策略优化
        if self.strategy == "hybrid":
            optimized_messages = self._hybrid_strategy(normal_messages)
        elif self.strategy == "token_budget":
            optimized_messages = self._token_budget_strategy(normal_messages)
        elif self.strategy == "window_size":
            optimized_messages = self._window_size_strategy(normal_messages)
        else:
            logger.warning(f"未知策略: {self.strategy}, 使用 hybrid")
            optimized_messages = self._hybrid_strategy(normal_messages)
        
        # 合并系统提示和优化后的消息
        final_messages = system_messages + optimized_messages
        
        optimized_token_count = self.count_messages_tokens(final_messages)
        removed_count = len(normal_messages) - len(optimized_messages)
        
        stats = {
            "original_count": len(normal_messages),
            "optimized_count": len(optimized_messages),
            "removed_count": removed_count,
            "original_tokens": original_token_count,
            "optimized_tokens": optimized_token_count,
            "saved_tokens": original_token_count - optimized_token_count,
            "strategy_used": self.strategy,
        }
        
        if removed_count > 0:
            logger.info(
                f"上下文优化完成 | "
                f"移除 {removed_count} 条消息 | "
                f"Token: {original_token_count} -> {optimized_token_count} "
                f"(节省 {stats['saved_tokens']})"
            )
        else:
            logger.debug(
                f"上下文无需优化 | "
                f"消息数: {len(optimized_messages)} | "
                f"Token: {optimized_token_count}"
            )
        
        return final_messages, stats
    
    def _hybrid_strategy(self, messages: List[Dict]) -> List[Dict]:
        """
        混合策略: Token 预算 + 最小轮数保证
        
        规则:
        1. 至少保留 min_keep_turns 轮对话
        2. 总 token 数不超过 max_tokens
        3. 优先保留最近的消息
        """
        if len(messages) <= self.min_keep_turns * 2:
            # 消息数少于最小保留轮数*2(user+assistant),直接返回
            return messages
        
        # 从后往前保留消息(最近的优先)
        kept_messages = []
        current_tokens = 0
        
        # 先确保至少保留 min_keep_turns 轮
        min_keep_count = min(self.min_keep_turns * 2, len(messages))
        recent_messages = messages[-min_keep_count:]
        
        for msg in reversed(recent_messages):
            msg_tokens = self.count_message_tokens(msg)
            if current_tokens + msg_tokens <= self.max_tokens:
                kept_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                # 如果连最小保留都超出 token 限制,强制保留但记录警告
                logger.warning(
                    f"最小保留轮数的 token 数 ({current_tokens + msg_tokens}) "
                    f"超过限制 ({self.max_tokens}), 强制保留"
                )
                kept_messages.insert(0, msg)
                current_tokens += msg_tokens
        
        # 尝试添加更多历史消息(如果还有 token 预算)
        remaining_messages = messages[:-min_keep_count]
        for msg in reversed(remaining_messages):
            msg_tokens = self.count_message_tokens(msg)
            if current_tokens + msg_tokens <= self.max_tokens:
                kept_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        return kept_messages
    
    def _token_budget_strategy(self, messages: List[Dict]) -> List[Dict]:
        """
        Token 预算策略: 严格控制 token 数量
        
        规则:
        1. 总 token 数不超过 max_tokens
        2. 从最旧的消息开始移除
        3. 保持对话完整性(成对移除)
        """
        if not messages:
            return []
        
        total_tokens = self.count_messages_tokens(messages)
        
        if total_tokens <= self.max_tokens:
            return messages
        
        # 从前往后移除消息,直到满足 token 限制
        kept_messages = messages.copy()
        
        while len(kept_messages) >= 2:  # 至少保留一轮对话
            # 移除最旧的一对消息 (user + assistant)
            if len(kept_messages) >= 2:
                removed_tokens = (
                    self.count_message_tokens(kept_messages[0]) +
                    self.count_message_tokens(kept_messages[1])
                )
                kept_messages = kept_messages[2:]
                total_tokens -= removed_tokens
                
                if total_tokens <= self.max_tokens:
                    break
        
        # 如果还是超限,继续单条移除(但至少保留最后一轮)
        while total_tokens > self.max_tokens and len(kept_messages) > 2:
            removed_tokens = self.count_message_tokens(kept_messages[0])
            kept_messages = kept_messages[1:]
            total_tokens -= removed_tokens
        
        return kept_messages
    
    def _window_size_strategy(self, messages: List[Dict]) -> List[Dict]:
        """
        滑动窗口策略: 固定保留最近 N 轮对话
        
        规则:
        1. 保留最近 window_size 轮对话
        2. 不考虑 token 数量
        """
        if len(messages) <= self.window_size * 2:
            return messages
        
        # 保留最后 window_size * 2 条消息
        return messages[-(self.window_size * 2):]
    
    def get_context_stats(self, messages: List[Dict]) -> Dict:
        """
        获取上下文统计信息
        
        Args:
            messages: 消息列表
            
        Returns:
            统计信息字典
        """
        total_tokens = self.count_messages_tokens(messages)
        
        # 按角色统计
        role_stats = {}
        for msg in messages:
            role = msg.get("role", "unknown")
            if role not in role_stats:
                role_stats[role] = {"count": 0, "tokens": 0}
            role_stats[role]["count"] += 1
            role_stats[role]["tokens"] += self.count_message_tokens(msg)
        
        return {
            "total_messages": len(messages),
            "total_tokens": total_tokens,
            "role_breakdown": role_stats,
            "token_limit": self.max_tokens,
            "usage_percentage": round((total_tokens / self.max_tokens) * 100, 2) if self.max_tokens > 0 else 0,
        }
