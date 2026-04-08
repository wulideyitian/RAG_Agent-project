"""
多格式文档分块适配 - 使用示例
演示如何使用增强版的解析器和分块器
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.loader.parsers.pdf_parser import PDFParser
from core.loader.parsers.docx_parser import DOCXParser
from core.loader.parsers.md_parser import MarkdownParser
from core.preprocessing.text_splitter import TextSplitterService


def example_pdf_processing():
    """PDF 处理示例"""
    print("=" * 60)
    print("PDF 处理示例")
    print("=" * 60)
    
    pdf_path = Path("data/惠普笔记本使用指南.pdf")
    
    if not pdf_path.exists():
        print(f"文件不存在: {pdf_path}")
        return
    
    # 1. 使用增强版解析器（启用版式清理）
    parser = PDFParser(enable_layout_cleaning=True)
    documents = parser.parse(str(pdf_path))
    
    print(f"\n解析结果:")
    print(f"  - 文档数量: {len(documents)}")
    if documents:
        print(f"  - 总页数: {documents[0].metadata.get('total_pages', 'N/A')}")
        print(f"  - 是否已清理版式: {documents[0].metadata.get('layout_cleaned', False)}")
        print(f"  - 文本长度: {len(documents[0].page_content)}")
    
    # 2. 使用格式感知分块
    splitter = TextSplitterService()
    chunks = splitter.format_aware_split(documents, source_format="pdf")
    
    print(f"\n分块结果:")
    print(f"  - 块数量: {len(chunks)}")
    if chunks:
        print(f"  - 平均块大小: {sum(len(c.page_content) for c in chunks) / len(chunks):.0f}")
        print(f"  - 优化标记: {chunks[0].metadata.get('format_optimized', 'N/A')}")
    
    # 3. 显示前几个块的预览
    print(f"\n前3个块预览:")
    for i, chunk in enumerate(chunks[:3], 1):
        preview = chunk.page_content[:100].replace('\n', ' ')
        print(f"  块 {i}: {preview}...")


def example_docx_processing():
    """Word 处理示例"""
    print("\n" + "=" * 60)
    print("Word 处理示例")
    print("=" * 60)
    
    docx_path = Path("data/test_document.docx")
    
    if not docx_path.exists():
        print(f"文件不存在: {docx_path}")
        return
    
    # 1. 使用增强版解析器（启用结构提取）
    parser = DOCXParser(enable_structure_extraction=True)
    documents = parser.parse(str(docx_path))
    
    print(f"\n解析结果:")
    print(f"  - 文档数量: {len(documents)}")
    if documents:
        # 统计标题层级
        heading_levels = [doc.metadata.get('heading_level', 0) for doc in documents]
        print(f"  - 标题层级分布: {dict(zip(*zip(*[(l, heading_levels.count(l)) for l in set(heading_levels)])))}")
    
    # 2. 使用格式感知分块
    splitter = TextSplitterService()
    chunks = splitter.format_aware_split(documents, source_format="docx")
    
    print(f"\n分块结果:")
    print(f"  - 块数量: {len(chunks)}")
    if chunks:
        print(f"  - 优化标记: {chunks[0].metadata.get('format_optimized', 'N/A')}")
        # 显示标题信息
        for i, chunk in enumerate(chunks[:3], 1):
            heading_text = chunk.metadata.get('heading_text', '无标题')
            heading_level = chunk.metadata.get('heading_level', 0)
            print(f"  块 {i}: [{heading_level}级标题] {heading_text}")


def example_md_processing():
    """Markdown 处理示例"""
    print("\n" + "=" * 60)
    print("Markdown 处理示例")
    print("=" * 60)
    
    md_path = Path("data/fault_cases.md")
    
    if not md_path.exists():
        print(f"文件不存在: {md_path}")
        return
    
    # 1. 使用增强版解析器（启用层级分块）
    parser = MarkdownParser(enable_hierarchical_splitting=True, min_heading_level=2)
    documents = parser.parse(str(md_path))
    
    print(f"\n解析结果:")
    print(f"  - 文档数量: {len(documents)}")
    if documents:
        # 统计标题层级
        heading_levels = [doc.metadata.get('heading_level', 0) for doc in documents]
        level_counts = {}
        for level in heading_levels:
            level_counts[level] = level_counts.get(level, 0) + 1
        print(f"  - 标题层级分布: {level_counts}")
    
    # 2. 使用格式感知分块
    splitter = TextSplitterService()
    chunks = splitter.format_aware_split(documents, source_format="md")
    
    print(f"\n分块结果:")
    print(f"  - 块数量: {len(chunks)}")
    if chunks:
        print(f"  - 优化标记: {chunks[0].metadata.get('format_optimized', 'N/A')}")
        # 显示标题信息
        for i, chunk in enumerate(chunks[:5], 1):
            heading_text = chunk.metadata.get('heading_text', '无标题')
            heading_level = chunk.metadata.get('heading_level', 0)
            parent_heading = chunk.metadata.get('parent_heading', '')
            preview = f"[{heading_level}级标题] {heading_text}"
            if parent_heading:
                preview += f" (父: {parent_heading})"
            print(f"  块 {i}: {preview}")


def example_comparison():
    """对比不同配置的效果"""
    print("\n" + "=" * 60)
    print("配置对比示例")
    print("=" * 60)
    
    # 创建测试文本
    test_text = """# 第一章 概述

这是第一章的介绍内容。包含了很多重要的信息。

## 1.1 背景

随着科技的发展，笔记本电脑已经成为我们日常生活中不可或缺的工具。

### 1.1.1 历史发展

笔记本电脑的历史可以追溯到20世纪80年代。

## 1.2 主要功能

现代笔记本电脑具有多种功能：

1. 办公处理
2. 娱乐休闲
3. 学习研究

# 第二章 硬件

## 2.1 CPU

中央处理器是电脑的核心。

## 2.2 内存

内存影响电脑的运行速度。"""
    
    from langchain_core.documents import Document
    
    # 方法1: 传统方式
    print("\n方法1: 传统自适应分块")
    splitter = TextSplitterService()
    chunks_old = splitter.adaptive_split(test_text, source="test.md")
    print(f"  - 块数量: {len(chunks_old)}")
    print(f"  - 平均大小: {sum(len(c.page_content) for c in chunks_old) / len(chunks_old):.0f}")
    
    # 方法2: 格式感知分块（Markdown）
    print("\n方法2: Markdown 格式感知分块")
    doc = Document(page_content=test_text, metadata={"source": "test.md"})
    chunks_new = splitter.format_aware_split([doc], source_format="md")
    print(f"  - 块数量: {len(chunks_new)}")
    print(f"  - 平均大小: {sum(len(c.page_content) for c in chunks_new) / len(chunks_new):.0f}")
    
    # 显示元数据差异
    if chunks_new and 'heading_level' in chunks_new[0].metadata:
        print(f"  - 包含标题层级: ✓")
        for i, chunk in enumerate(chunks_new[:3], 1):
            heading = chunk.metadata.get('heading_text', '')
            print(f"    块{i}: {heading}")


if __name__ == "__main__":
    print("多格式文档分块适配 - 使用示例\n")
    
    # 运行示例
    example_pdf_processing()
    example_docx_processing()
    example_md_processing()
    example_comparison()
    
    print("\n" + "=" * 60)
    print("示例运行完成!")
    print("=" * 60)
