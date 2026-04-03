"""
文本清洗器
清理乱码、特殊符号、多余空白等
"""
import re
from app.utils.logger_handler import logger


class TextCleaner:
    """文本清洗工具类"""
    
    def __init__(self):
        # 定义清洗规则
        self.clean_rules = {
            'remove_null_chars': ('\ufffd', ''),  # 替换无效字符
            'remove_tabs': ('\t', ' '),  # 制表符转空格
            'compress_newlines': (r'\n{3,}', '\n\n'),  # 压缩连续空行
            'remove_control_chars': (r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', ''),  # 控制字符
        }
    
    def clean(self, text: str, file_type: str = 'txt') -> str:
        """
        清洗文本
        :param text: 原始文本
        :param file_type: 文件类型
        :return: 清洗后的文本
        """
        if not text:
            return ""
        
        # 通用清洗
        text = self._apply_common_cleaning(text)
        
        # 根据文件类型特殊处理
        if file_type in ['txt', 'md']:
            text = self._apply_text_specific_cleaning(text)
        
        # 首尾空白清理
        text = text.strip()
        
        return text
    
    def _apply_common_cleaning(self, text: str) -> str:
        """应用通用清洗规则"""
        # 替换无效字符
        text = text.replace(*self.clean_rules['remove_null_chars'])
        
        # 去除控制字符
        text = re.sub(
            self.clean_rules['remove_control_chars'][0],
            self.clean_rules['remove_control_chars'][1],
            text
        )
        
        return text
    
    def _apply_text_specific_cleaning(self, text: str) -> str:
        """应用针对 TXT/Markdown 的特殊清洗"""
        # 制表符转空格
        text = text.replace(*self.clean_rules['remove_tabs'])
        
        # 压缩连续空行
        text = re.sub(
            self.clean_rules['compress_newlines'][0],
            self.clean_rules['compress_newlines'][1],
            text
        )
        
        return text
    
    def deep_clean(self, text: str) -> str:
        """
        深度清洗（更激进的清理策略）
        :param text: 原始文本
        :return: 深度清洗后的文本
        """
        # 基础清洗
        text = self.clean(text)
        
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除 URL（可选，根据需要保留）
        # text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 移除邮箱地址
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # 规范化标点符号（中文标点转英文标点，可选）
        # text = re.sub(r'[,.!?,:;"\'\(\)]', lambda m: m.group(0).translate(str.maketrans('.,!?,:;""\'()', '.,!?,:;"\'()')), text)
        
        return text
    
    def validate_quality(self, text: str, min_length: int = 50) -> bool:
        """
        简单验证文本质量
        :param text: 待验证文本
        :param min_length: 最小有效长度
        :return: True 如果质量合格
        """
        if not text or len(text.strip()) < min_length:
            return False
        
        # 检查是否大部分是特殊字符
        valid_char_ratio = sum(1 for c in text if c.isalnum() or c.isspace()) / max(len(text), 1)
        if valid_char_ratio < 0.6:
            logger.warning(f"文本有效字符比例过低：{valid_char_ratio}")
            return False
        
        return True
