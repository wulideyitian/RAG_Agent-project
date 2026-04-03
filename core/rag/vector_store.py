"""
向量库管理服务
负责向量库的持久化和操作
"""
from langchain_chroma import Chroma
from app.utils.config_handler import chroma_conf
from app.utils.path_tool import get_abs_path
from core.embedding.embed_model import EmbedModelService
from core.preprocessing.text_splitter import TextSplitterService
from core.loader.document_loader import UnifiedDocumentLoader
from app.utils.file_handler import listdir_with_allowed_type, get_file_md5_hex
from app.utils.logger_handler import logger
import os


class VectorStoreService:
    """向量库管理服务"""
    
    def __init__(self):
        self.embed_service = EmbedModelService()
        self.spliter = TextSplitterService()
        self.doc_loader = UnifiedDocumentLoader()
        
        # 初始化向量库
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],
            embedding_function=self.embed_service.model,
            persist_directory=get_abs_path(chroma_conf["persist_directory"]),
        )
    
    def get_retriever(self):
        """获取检索器"""
        return self.vector_store.as_retriever(
            search_kwargs={"k": chroma_conf.get("k", 3)}
        )
    
    def load_documents(self):
        """
        从数据文件夹加载文档到向量库
        """
        allowed_files_path = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_knowledge_file_type"]),
        )
        
        for path in allowed_files_path:
            self._load_single_document(path)
    
    def _load_single_document(self, filepath: str):
        """加载单个文档"""
        try:
            # 检查 MD5 是否已处理
            md5_hex = get_file_md5_hex(filepath)
            if self._check_md5_exists(md5_hex):
                logger.info(f"[加载知识库]{filepath}内容已存在，跳过")
                return
            
            # 加载文档
            result = self.doc_loader.load_from_path(filepath)
            
            if result["status"] != "success" or not result["text"].strip():
                logger.warning(f"[加载知识库]{filepath}无有效内容，跳过")
                return
            
            from langchain_core.documents import Document
            doc = Document(
                page_content=result["text"],
                metadata={"source": filepath, "file_type": result["file_type"]}
            )
            
            # 分块
            chunks = self.spliter.split_documents([doc])
            
            if not chunks:
                logger.warning(f"[加载知识库]{filepath}分块后无有效内容，跳过")
                return
            
            # 存入向量库
            self.vector_store.add_documents(
                documents=chunks, 
                ids=[f"{md5_hex}_{i}" for i in range(len(chunks))]
            )
            
            # 记录 MD5
            self._save_md5(md5_hex)
            
            logger.info(f"[加载知识库]{filepath}加载成功")
            
        except Exception as e:
            logger.error(f"[加载知识库]{filepath}失败：{str(e)}", exc_info=True)
    
    def _check_md5_exists(self, md5_hex: str) -> bool:
        """检查 MD5 是否已存在"""
        md5_file = get_abs_path(chroma_conf.get("md5_hex_store", "md5.txt"))
        
        if not os.path.exists(md5_file):
            open(md5_file, "w", encoding="utf-8").close()
            return False
        
        with open(md5_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() == md5_hex:
                    return True
        return False
    
    def _save_md5(self, md5_hex: str):
        """保存 MD5 记录"""
        md5_file = get_abs_path(chroma_conf.get("md5_hex_store", "md5.txt"))
        with open(md5_file, "a", encoding="utf-8") as f:
            f.write(md5_hex + "\n")
