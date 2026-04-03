"""
文件管理 API 路由
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from core.api.schemas.response import APIResponse
from app.utils.logger_handler import logger

router = APIRouter(prefix="/api/files", tags=["文件管理"])


@router.post("/upload", response_model=APIResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    上传文件到知识库
    """
    try:
        from core.rag.vector_store import VectorStoreService
        
        # 验证文件类型
        allowed_types = ['.pdf', '.txt', '.docx', '.md']
        file_ext = '.' + file.filename.split('.')[-1].lower()
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型：{file_ext}"
            )
        
        # 保存临时文件
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # 加载到向量库
            vector_store = VectorStoreService()
            
            # 这里简化处理，实际应该异步任务
            result = vector_store.doc_loader.load_from_path(tmp_path)
            
            if result["status"] == "success":
                logger.info(f"文件{file.filename}上传成功")
                return APIResponse(
                    success=True,
                    message="文件上传成功",
                    data={"filename": file.filename, "type": file_ext}
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"文件解析失败：{result['error_msg']}"
                )
                
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传异常：{str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
