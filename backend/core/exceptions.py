"""自定义异常：权限不足、文件解析失败."""

from typing import Any, Optional

from config.response_codes import (
    BAD_REQUEST,
    FORBIDDEN,
    INTERNAL_ERROR,
    UNAUTHORIZED,
)


class AppError(Exception):
    """应用基础异常。"""

    def __init__(
        self,
        message: str,
        code: int = INTERNAL_ERROR,
        status_code: int = 500,
        description: str = "",
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.description = description
        super().__init__(message)


class PermissionDeniedError(AppError):
    """用户缺少所需权限时抛出。"""

    def __init__(self, message: str = "权限不足", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            code=FORBIDDEN,
            status_code=403,
            description="权限不足",
        )
        self.detail = detail


class FileParseError(AppError):
    """文档解析失败时抛出。"""

    def __init__(self, message: str = "文件解析失败", filename: Optional[str] = None):
        super().__init__(
            message=message,
            code=BAD_REQUEST,
            status_code=422,
            description="文件解析失败",
        )
        self.filename = filename


class AuthenticationError(AppError):
    """认证失败时抛出。"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            code=UNAUTHORIZED,
            status_code=401,
            description="认证失败",
        )


class ValidationError(AppError):
    """输入校验失败时抛出。"""

    def __init__(self, message: str = "参数校验失败"):
        super().__init__(
            message=message,
            code=BAD_REQUEST,
            status_code=400,
            description="参数校验失败",
        )
