"""
全局异常处理器
定义统一的 HTTP 异常基类和常见的业务异常
"""
from fastapi import HTTPException, status
from typing import Any, Optional


class BaseAPIException(HTTPException):
    """
    API 基础异常类
    所有自定义 HTTP 异常都应继承此类
    """
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        message: str = "服务器内部错误",
        error_code: Optional[str] = None,
        detail: Optional[Any] = None,
    ):
        super().__init__(status_code=status_code, detail=detail or message)
        self.message = message
        self.error_code = error_code or f"ERR_{status_code}"


class ValidationException(BaseAPIException):
    """数据验证异常"""
    
    def __init__(self, message: str = "数据验证失败", detail: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error_code="ERR_VALIDATION",
            detail=detail,
        )


class NotFoundException(BaseAPIException):
    """资源未找到异常"""
    
    def __init__(self, message: str = "资源未找到", detail: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="ERR_NOT_FOUND",
            detail=detail,
        )


class AuthenticationException(BaseAPIException):
    """认证异常"""
    
    def __init__(self, message: str = "认证失败", detail: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="ERR_AUTHENTICATION",
            detail=detail,
        )


class AuthorizationException(BaseAPIException):
    """授权异常"""
    
    def __init__(self, message: str = "无权访问", detail: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="ERR_AUTHORIZATION",
            detail=detail,
        )


class ConflictException(BaseAPIException):
    """冲突异常"""
    
    def __init__(self, message: str = "资源冲突", detail: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code="ERR_CONFLICT",
            detail=detail,
        )


class ServiceUnavailableException(BaseAPIException):
    """服务不可用异常"""
    
    def __init__(self, message: str = "服务暂时不可用", detail: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            error_code="ERR_SERVICE_UNAVAILABLE",
            detail=detail,
        )
