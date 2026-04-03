"""
文档加载模块
负责读取各种格式的文档 (PDF/DOCX/TXT/Markdown 等)
"""
from core.loader.document_loader import UnifiedDocumentLoader
from core.loader.parsers.pdf_parser import PDFParser
from core.loader.parsers.docx_parser import DOCXParser
from core.loader.parsers.txt_parser import TXTParser
from core.loader.parsers.md_parser import MarkdownParser

__all__ = [
    "UnifiedDocumentLoader",
    "PDFParser",
    "DOCXParser",
    "TXTParser",
    "MarkdownParser",
]
