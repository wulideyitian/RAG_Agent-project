"""
PDF 版式清理器
专门处理 PDF 文档的版式干扰问题：
- 页眉页脚重复
- 页码干扰
- 断行合并
- 栏位错位修复
"""
import re
from typing import List, Optional
from app.utils.logger_handler import logger


class PDFLayoutCleaner:
    """PDF 版式清理器"""
    
    def __init__(self):
        # 常见页码模式
        self.page_number_patterns = [
            r'^\s*第\s*\d+\s*页\s*$',           # 第 1 页
            r'^\s*Page\s*\d+\s*(of\s*\d+)?\s*$',  # Page 1 of 10
            r'^\s*-\s*\d+\s*-\s*$',             # - 1 -
            r'^\s*\d+\s*/\s*\d+\s*$',           # 1 / 10
            r'^\s*\[\s*\d+\s*\]\s*$',           # [1]
        ]
        
        # 常见页眉页脚关键词
        self.header_footer_keywords = [
            r'机密', r'内部资料', r'CONFIDENTIAL',
            r'版权所有', r'Copyright', r'©\s*\d{4}',
            r'www\.', r'http[s]?://',
        ]
    
    def clean_layout_artifacts(self, text: str) -> str:
        """
        清理 PDF 版式伪影（主入口）
        :param text: 原始文本
        :return: 清理后的文本
        """
        if not text or not text.strip():
            return text
        
        logger.info("开始清理 PDF 版式伪影")
        
        # 1. 移除页码
        text = self._remove_page_numbers(text)
        
        # 2. 合并被断行的句子
        text = self.merge_broken_lines(text)
        
        # 3. 【新增】移除段落间的单换行，只保留双换行作为段落分隔
        # 匹配: 句号/感叹号/问号 + 单换行 + 非空行
        # 替换为: 标点 + 无换行（直接连接）
        text = re.sub(r'([。！？.!?])\n([^\n])', r'\1\2', text)
        
        # 4. 压缩多余空行（3个以上换行压缩为2个）
        text = self._compress_blank_lines(text)
        
        # 5. 清理孤立的短行（可能是页眉页脚残留）
        text = self._remove_orphaned_short_lines(text)
        
        logger.info("PDF 版式清理完成")
        return text
    
    def merge_broken_lines(self, text: str) -> str:
        """
        使用正则表达式合并句子内部的断行
        规则: 如果换行符前后都是中文字符或非段落结束标点,则替换为空格
        :param text: 原始文本
        :return: 合并后的文本
        """
        if not text:
            return text
        
        # 策略1: 合并中文句子内部的断行
        # 匹配: 中文字符/非标点 + 换行 + 中文字符
        # 排除: 段落结束标点(。！？.!?等)后面的换行
        pattern_broken_sentence = r'([^。！？.!?:;\n\s])\n([^\n。！？.!?:;\s])'
        text = re.sub(pattern_broken_sentence, r'\1 \2', text)
        
        # 策略2: 处理连续多个断行(可能是列表或特殊格式,保留一个换行)
        # 将3个或更多连续换行压缩为2个
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 策略3: 清理空行前后的多余空格
        text = re.sub(r' *\n *', '\n', text)
        
        return text.strip()
    
    def _should_merge_lines(self, current_line: str, next_line: str) -> bool:
        """
        [已废弃] 判断两行是否应该合并
        注意: 此方法已被 merge_broken_lines 中的正则表达式替代
        保留此方法仅为向后兼容
        :param current_line: 当前行
        :param next_line: 下一行
        :return: True 如果应该合并
        """
        # 如果下一行是空行，不合并
        if not next_line:
            return False
        
        # 如果当前行以段落结束符结尾，不合并
        paragraph_endings = ['。', '！', '？', '.', '!', '?', '…', '」', '』', ')', '）']
        if current_line and current_line[-1] in paragraph_endings:
            return False
        
        # 如果当前行以列表标记开头，不合并
        list_markers = ['-', '*', '•', '→', '■', '□', '●', '○']
        if current_line and current_line[0] in list_markers:
            return False
        
        # 如果下一行以大写字母开头且当前行以句号结尾（英文句子），不合并
        if next_line[0].isupper() and current_line and current_line[-1] == '.':
            return False
        
        # 如果下一行是标题格式（如 "## 标题" 或 "第一章"），不合并
        if re.match(r'^#{1,6}\s+', next_line) or re.match(r'^第[一二三四五六七八九十\d]+章', next_line):
            return False
        
        # 默认情况：如果当前行不以标点结尾，且长度不太长，则合并
        if len(current_line) < 100 and not re.search(r'[。！？.!?:;]$', current_line):
            return True
        
        return False
    
    def detect_and_remove_headers_footers(self, pages: List[str]) -> List[str]:
        """
        检测并移除跨页重复的页眉页脚
        :param pages: 每页的内容列表
        :return: 清理后的页面列表
        """
        if not pages or len(pages) < 2:
            return pages
        
        logger.info(f"检测 {len(pages)} 页的重复页眉页脚")
        
        cleaned_pages = []
        
        # 提取每页的前3行和后3行作为候选页眉页脚
        header_candidates = []
        footer_candidates = []
        
        for page in pages:
            lines = page.strip().split('\n')
            # 优化：对于短页面（<=3行），只提取首尾各1行；长页面提取前3后3
            if len(lines) >= 4:
                header_candidates.append('\n'.join(lines[:3]))
                footer_candidates.append('\n'.join(lines[-3:]))
            elif len(lines) >= 2:
                # 短页面：只取第1行和最后1行
                header_candidates.append(lines[0])
                footer_candidates.append(lines[-1])
        
        # 找出重复出现的页眉页脚
        common_header = self._find_common_pattern(header_candidates)
        common_footer = self._find_common_pattern(footer_candidates)
        
        # 从每页中移除识别出的页眉页脚
        for page in pages:
            cleaned_page = page
            
            if common_header:
                # 移除页眉（页面开头部分）
                lines = cleaned_page.split('\n')
                # 将 common_header 按行分割，逐个匹配删除
                header_lines_to_remove = common_header.split('\n')
                cleaned_lines = []
                skip_indices = set()
                
                # 找到所有匹配的 header 行索引
                for hi, hline in enumerate(header_lines_to_remove):
                    for li, line in enumerate(lines):
                        if line.strip() == hline.strip() and li not in skip_indices:
                            skip_indices.add(li)
                            break
                
                # 保留非 header 行
                for li, line in enumerate(lines):
                    if li not in skip_indices:
                        cleaned_lines.append(line)
                
                cleaned_page = '\n'.join(cleaned_lines)
            
            if common_footer:
                # 移除页脚（页面结尾部分）
                lines = cleaned_page.split('\n')
                # 将 common_footer 按行分割，逐个匹配删除
                footer_lines_to_remove = common_footer.split('\n')
                cleaned_lines = []
                skip_indices = set()
                
                # 从后往前找匹配的 footer 行
                for fi, fline in enumerate(reversed(footer_lines_to_remove)):
                    for li in range(len(lines) - 1, -1, -1):
                        if lines[li].strip() == fline.strip() and li not in skip_indices:
                            skip_indices.add(li)
                            break
                
                # 保留非 footer 行
                for li, line in enumerate(lines):
                    if li not in skip_indices:
                        cleaned_lines.append(line)
                
                cleaned_page = '\n'.join(cleaned_lines)
            
            cleaned_pages.append(cleaned_page)
        
        logger.info(f"页眉页脚清理完成，识别到 {bool(common_header)} 个重复页眉, {bool(common_footer)} 个重复页脚")
        return cleaned_pages
    
    def _find_common_pattern(self, candidates: List[str], min_occurrence: int = 2) -> Optional[str]:
        """
        在候选列表中找出重复出现的模式
        :param candidates: 候选字符串列表
        :param min_occurrence: 最小出现次数
        :return: 最常见的模式，如果没有则返回 None
        """
        if not candidates:
            return None
        
        from collections import Counter
        counter = Counter(candidates)
        
        # 找出出现次数最多的
        most_common = counter.most_common(1)
        if most_common and most_common[0][1] >= min_occurrence:
            return most_common[0][0]
        
        return None
    
    def _remove_page_numbers(self, text: str) -> str:
        """
        移除页码
        :param text: 原始文本
        :return: 清理后的文本
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            is_page_number = False
            
            # 检查是否匹配页码模式
            for pattern in self.page_number_patterns:
                if re.match(pattern, stripped):
                    is_page_number = True
                    break
            
            if not is_page_number:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _compress_blank_lines(self, text: str) -> str:
        """
        压缩连续空行为最多两个
        :param text: 原始文本
        :return: 清理后的文本
        """
        # 将3个或更多连续换行符替换为2个
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text
    
    def _remove_orphaned_short_lines(self, text: str, max_length: int = 10) -> str:
        """
        移除孤立的短行（可能是页眉页脚残留）
        :param text: 原始文本
        :param max_length: 最大长度阈值
        :return: 清理后的文本
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 如果是空行，保留
            if not stripped:
                cleaned_lines.append(line)
                continue
            
            # 如果是很短的行，检查上下文
            if len(stripped) <= max_length:
                # 检查是否是孤立行（前后都是空行或边界）
                prev_empty = (i == 0) or (not lines[i-1].strip())
                next_empty = (i == len(lines) - 1) or (not lines[i+1].strip() if i+1 < len(lines) else True)
                
                # 如果是孤立短行，且包含页眉页脚关键词，则移除
                if prev_empty and next_empty:
                    is_header_footer = any(
                        re.search(keyword, stripped, re.IGNORECASE) 
                        for keyword in self.header_footer_keywords
                    )
                    if is_header_footer:
                        logger.debug(f"移除孤立短行（疑似页眉页脚）: {stripped}")
                        continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def clean_multiple_pages(self, pages: List[str]) -> str:
        """
        清理多页 PDF 内容（完整流程）
        :param pages: 每页内容的列表
        :return: 合并并清理后的完整文本
        """
        if not pages:
            return ""
        
        logger.info(f"开始清理 {len(pages)} 页 PDF 内容")
        
        # 1. 逐页清理版式伪影
        cleaned_pages = [self.clean_layout_artifacts(page) for page in pages]
        
        # 2. 检测并移除跨页重复的页眉页脚
        cleaned_pages = self.detect_and_remove_headers_footers(cleaned_pages)
        
        # 3. 合并所有页面
        full_text = '\n\n'.join(cleaned_pages)
        
        # 4. 最后一次全局清理
        full_text = self._compress_blank_lines(full_text)
        
        logger.info(f"PDF 多页清理完成，最终文本长度: {len(full_text)}")
        return full_text
