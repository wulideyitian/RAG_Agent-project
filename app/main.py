# FastAPI 入口（创建实例、注册路由/中间件）
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.api.schemas.response import APIResponse
from core.api.routes.chat_routes import router as chat_router
from core.api.routes.file_routes import router as file_router
from core.api.routes.rag_routes import router as rag_router
from app.utils.logger_handler import logger
import time



# 创建 FastAPI 应用
app = FastAPI(
    title="笔记本智能问答助手 API",
    description="基于 RAG 和 Agent 的智能客服系统，提供笔记本电脑咨询、故障诊断、选购推荐等服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有 HTTP 请求的日志"""
    start_time = time.time()
    
    # 记录请求信息
    logger.info(f"{request.method} {request.url.path} - 开始处理")
    
    try:
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = round((time.time() - start_time) * 1000, 2)  # 毫秒
        
        # 记录响应信息
        logger.info(
            f"{request.method} {request.url.path} - "
            f"状态码：{response.status_code} - "
            f"耗时：{process_time}ms"
        )
        
        # 在响应头中添加处理时间
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        # 记录异常信息
        logger.error(f"{request.method} {request.url.path} - 处理异常：{str(e)}")
        raise


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常捕获：{request.method} {request.url.path} - 错误：{str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "error": str(exc) if app.debug else "请稍后重试"
        },
    )


# 健康检查
@app.get("/api/health", response_model=APIResponse)
async def health_check():
    """
    全局健康检查接口
    """
    return APIResponse(
        success=True,
        message="服务运行正常",
        data={"status": "healthy"}
    )


# 注册路由（使用新的核心模块路由）
app.include_router(chat_router)
app.include_router(file_router)
app.include_router(rag_router)


if __name__ == "__main__":
    import uvicorn
    # 启动服务
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
