import os
import hashlib
import chardet
from typing import Union, BinaryIO
from app.utils.logger_handler import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    PythonLoader,
)
from langchain_community.document_loaders.word_document import Docx2txtLoader
import re


class FileValidationError(Exception):
    """文件验证异常：魔数检测失败或文件损坏"""
    pass


class DocumentParseError(Exception):
    """文档解析异常"""
    pass


# 文件类型魔数定义（用于合法性校验）
FILE_MAGIC_NUMBERS = {
    'pdf': [b'%PDF-'],
    'docx': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],  # DOCX 是 ZIP 格式
    'txt': [],  # TXT 无固定魔数，通过编码检测
    'md': [],   # Markdown 无固定魔数，通过扩展名识别
}


def get_file_md5_hex(filepath: str):     # 获取文件的 md5 的十六进制字符串

    if not os.path.exists(filepath):
        logger.error(f"[md5 计算] 文件{filepath}不存在")
        return None

    if not os.path.isfile(filepath):
        logger.error(f"[md5 计算] 路径{filepath}不是文件")
        return None

    md5_obj = hashlib.md5()

    chunk_size = 4096       # 4KB 分片，避免文件过大爆内存
    try:
        with open(filepath, "rb") as f:     # 必须二进制读取
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)

            """
            chunk = f.read(chunk_size)
            while chunk:
                
                md5_obj.update(chunk)
                chunk = f.read(chunk_size)
            """
            md5_hex = md5_obj.hexdigest()
            return md5_hex
    except Exception as e:
        logger.error(f"计算文件{filepath}md5 失败，{str(e)}")
        return None


def listdir_with_allowed_type(path: str, allowed_types: tuple[str]):        # 返回文件夹内的文件列表（允许的文件后缀）
    files = []

    if not os.path.isdir(path):
        logger.error(f"[listdir_with_allowed_type]{path}不是文件夹")
        return ()

    for f in os.listdir(path):
        if f.endswith(allowed_types):
            files.append(os.path.join(path, f))

    return tuple(files)


def validate_file_magic(filepath: str, file_type: str) -> bool:
    """
    验证文件魔数，确保文件合法且未损坏
    :param filepath: 文件路径
    :param file_type: 文件类型
    :return: True 如果验证通过
    :raises FileValidationError: 验证失败时抛出异常
    """
    expected_magic = FILE_MAGIC_NUMBERS.get(file_type, [])
    
    # TXT 和 Markdown 不需要魔数验证
    if not expected_magic:
        return True
    
    try:
        with open(filepath, 'rb') as f:
            header = f.read(16)  # 读取文件头 16 字节
            
            for magic in expected_magic:
                if header.startswith(magic):
                    return True
            
            raise FileValidationError(
                f"文件{filepath}魔数验证失败：期望{expected_magic}，实际{header[:8]}"
            )
    except FileNotFoundError:
        raise FileValidationError(f"文件{filepath}不存在")
    except PermissionError:
        raise FileValidationError(f"文件{filepath}无权限读取")
    except Exception as e:
        if isinstance(e, FileValidationError):
            raise
        raise FileValidationError(f"文件{filepath}读取失败：{str(e)}")


def detect_encoding(filepath: str) -> str:
    """
    检测文件编码
    :param filepath: 文件路径
    :return: 编码格式
    """
    try:
        with open(filepath, 'rb') as f:
            raw_data = f.read(1024 * 4)  # 读取前 4KB
            result = chardet.detect(raw_data)
            encoding = result['encoding'] if result['encoding'] else 'utf-8'
            confidence = result['confidence'] if result['confidence'] else 0
            
            if confidence < 0.7:
                logger.warning(f"文件{filepath}编码检测结果置信度较低：{confidence}，使用默认编码{encoding}")
            
            return encoding
    except Exception as e:
        logger.error(f"检测文件{filepath}编码失败：{str(e)}，使用默认 UTF-8")
        return 'utf-8'


def clean_text(text: str, file_type: str) -> str:
    """
    清理文本中的乱码、特殊符号、多余空白等
    :param text: 原始文本
    :param file_type: 文件类型
    :return: 清理后的文本
    """
    # 替换无效字符（Unicode 替换字符）
    text = text.replace('\ufffd', '')
    
    if file_type in ['txt', 'md']:
        # 去除制表符
        text = text.replace('\t', ' ')
        # 压缩连续空行为最多 2 个
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 清理特殊符号（保留常见的标点）
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # 清理首尾空白
    text = text.strip()
    
    return text


def pdf_loader(filepath: str, passwd=None) -> list[Document]:
    """
    PDF 文件加载器
    :param filepath: 文件路径
    :param passwd: 密码（可选）
    :return: Document 列表
    """
    try:
        # 验证文件合法性
        validate_file_magic(filepath, 'pdf')
        
        loader = PyPDFLoader(filepath, passwd)
        documents = loader.load()
        
        # 过滤重复页眉页脚（简单实现：检测连续页面的重复内容）
        cleaned_docs = []
        prev_content = ""
        for doc in documents:
            current_content = doc.page_content
            # 如果当前内容与上一页高度相似（超过 80%），则跳过
            if prev_content and current_content == prev_content:
                logger.info(f"PDF{filepath}中检测到重复页眉/页脚，已过滤")
                continue
            cleaned_docs.append(doc)
            prev_content = current_content
        
        return cleaned_docs
    except FileValidationError as e:
        logger.error(f"PDF 文件验证失败：{str(e)}")
        raise DocumentParseError(str(e))
    except Exception as e:
        logger.error(f"加载 PDF 文件{filepath}失败：{str(e)}")
        raise DocumentParseError(f"PDF 解析失败：{str(e)}")


def txt_loader(filepath: str) -> list[Document]:
    """
    TXT 文件加载器（带编码检测）
    :param filepath: 文件路径
    :return: Document 列表
    """
    try:
        # 检测文件编码
        encoding = detect_encoding(filepath)
        
        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        
        # 清理文本
        content = clean_text(content, 'txt')
        
        # 创建 Document 对象
        doc = Document(page_content=content, metadata={"source": filepath})
        return [doc]
    except Exception as e:
        logger.error(f"加载 TXT 文件{filepath}失败：{str(e)}")
        raise DocumentParseError(f"TXT 解析失败：{str(e)}")


def docx_loader(filepath: str) -> list[Document]:
    """
    Word 文件加载器（仅提取纯文本段落，跳过表格和图片）
    :param filepath: 文件路径
    :return: Document 列表
    """
    try:
        # 验证文件合法性
        validate_file_magic(filepath, 'docx')
        
        loader = Docx2txtLoader(filepath)
        documents = loader.load()
        
        if not documents:
            return []
        
        # 清理文本
        cleaned_content = clean_text(documents[0].page_content, 'txt')
        doc = Document(page_content=cleaned_content, metadata={"source": filepath})
        return [doc]
    except FileValidationError as e:
        logger.error(f"Word 文件验证失败：{str(e)}")
        raise DocumentParseError(str(e))
    except Exception as e:
        logger.error(f"加载 Word 文件{filepath}失败：{str(e)}")
        raise DocumentParseError(f"Word 解析失败：{str(e)}")


def md_loader(filepath: str) -> list[Document]:
    """
    Markdown 文件加载器（使用 UnstructuredMarkdownLoader）
    :param filepath: 文件路径
    :return: Document 列表
    """
    try:
        loader = UnstructuredMarkdownLoader(filepath)
        documents = loader.load()
        
        if not documents:
            return []
        
        # 清理文本
        cleaned_content = clean_text(documents[0].page_content, 'md')
        doc = Document(page_content=cleaned_content, metadata={"source": filepath})
        return [doc]
    except Exception as e:
        logger.error(f"加载 Markdown 文件{filepath}失败：{str(e)}")
        raise DocumentParseError(f"Markdown 解析失败：{str(e)}")

