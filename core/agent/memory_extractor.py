"""
记忆提取工具
从对话中自动提取关键信息并更新用户记忆
"""
import re
from typing import Dict, Any, List, Optional


class MemoryExtractor:
    """记忆提取器"""
    
    def __init__(self):
        # 预算模式匹配
        self.budget_patterns = [
            r'预算\s*[:：]?\s*(\d+[-\d 千]+)',
            r'价格\s*[:：]?\s*(\d+[-\d 千]+)',
            r'价位\s*[:：]?\s*(\d+[-\d 千]+)',
            r'(\d{3,4})\s*到\s*(\d{3,4})\s*元',
            r'(\d{3,4})[-~～](\d{3,4})\s*元',
        ]
        
        # 使用场景关键词
        self.scenario_keywords = [
            '游戏', '办公', '学习', '设计', '编程', '视频剪辑',
            '图形处理', '日常使用', '商务', '学生', '专业用途',
        ]
        
        # 地理位置关键词
        self.location_patterns = [
            r'(北京 | 上海 | 广州 | 深圳 | 杭州 | 南京 | 成都 | 武汉 | 西安 | 重庆)',
            r'在 (\w+ 市 |\w+ 省)',
            r'坐标 (\w+)',
        ]
    
    def extract_budget(self, text: str) -> Optional[str]:
        """从文本中提取预算信息"""
        for pattern in self.budget_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def extract_usage_scenario(self, text: str) -> Optional[str]:
        """从文本中提取使用场景"""
        for keyword in self.scenario_keywords:
            if keyword in text.lower():
                # 尝试获取更多上下文
                match = re.search(rf'(.{{0,20}}{keyword}.{{0,20}})', text)
                if match:
                    return match.group(1).strip()
                return keyword
        return None
    
    def extract_location(self, text: str) -> Optional[str]:
        """从文本中提取地理位置"""
        for pattern in self.location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def extract_preferences(self, text: str) -> Dict[str, Any]:
        """从文本中提取用户偏好"""
        preferences = {}
        
        # 品牌偏好
        brand_keywords = ['联想', '惠普', '戴尔', '华硕', '苹果', 'MacBook', 'ThinkPad']
        mentioned_brands = [brand for brand in brand_keywords if brand in text]
        if mentioned_brands:
            preferences['mentioned_brands'] = mentioned_brands
        
        # 配置偏好
        config_patterns = {
            'cpu': r'(i[3579]|R[579])\s*\d{4}',
            'ram': r'(\d{2})GB\s*内存',
            'storage': r'(\d{3})GB\s*(SSD|硬盘)',
            'gpu': r'(RTX|GTX)\s*\d{4}',
        }
        
        for key, pattern in config_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                preferences[key] = match.group(0)
        
        return preferences
    
    def extract_from_conversation(
        self,
        user_input: str,
        assistant_response: str = None,
    ) -> Dict[str, Any]:
        """
        从完整对话中提取记忆
        :param user_input: 用户输入
        :param assistant_response: 助手响应（可选）
        :return: 包含所有提取字段的字典
        """
        combined_text = f"{user_input}\n{assistant_response or ''}"
        
        result = {
            'budget': self.extract_budget(user_input),
            'usage_scenario': self.extract_usage_scenario(user_input),
            'location': self.extract_location(user_input),
            'preferences': self.extract_preferences(combined_text),
            'mentioned_models': [],
        }
        
        # 笔记本型号提取（简化版，实际应该用 NLP 模型）
        model_patterns = [
            r'(ThinkPad\s*\w+)',
            r'(MacBook\s*(Pro|Air)?)',
            r'(灵越\s*\w+)',
            r'(战\s*\d+\s*\w+)',
        ]
        
        for pattern in model_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    result['mentioned_models'].extend([' '.join(m) for m in matches])
                else:
                    result['mentioned_models'].extend(matches)
        
        # 过滤空值
        result = {k: v for k, v in result.items() if v and (isinstance(v, list) and len(v) > 0 or not isinstance(v, list))}
        
        return result
    
    def should_update_memory(
        self,
        current_memory: Dict[str, Any],
        extracted: Dict[str, Any],
    ) -> bool:
        """判断是否需要更新记忆"""
        # 如果有任何新信息，就更新
        for key, value in extracted.items():
            if key == 'mentioned_models':
                # 如果有新的型号提及
                existing = current_memory.get('mentioned_models', [])
                new_models = set(value) - set(existing)
                if new_models:
                    return True
            elif key == 'preferences':
                # 如果有新的偏好
                existing_prefs = current_memory.get('preferences', {})
                for pref_key, pref_value in value.items():
                    if existing_prefs.get(pref_key) != pref_value:
                        return True
            else:
                # 其他字段如果有值且不同
                if value and current_memory.get(key) != value:
                    return True
        
        return False
