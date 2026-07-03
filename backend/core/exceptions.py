"""自定义异常：权限不足、文件解析失败、租户不存在."""

from typing import Any, Optional


class AppError(Exception):
    """应用基础异常。"""

    def __init__(self, message: str, code: str = "APP_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class PermissionDeniedError(AppError):
    """用户缺少所需权限时抛出。"""

    def __init__(self, message: str = "权限不足", detail: Optional[Any] = None):
        super().__init__(message=message, code="PERMISSION_DENIED", status_code=403)
        self.detail = detail


class FileParseError(AppError):
    """文档解析失败时抛出。"""

    def __init__(self, message: str = "文件解析失败", filename: Optional[str] = None):
        super().__init__(message=message, code="FILE_PARSE_ERROR", status_code=422)
        self.filename = filename


class TenantNotFoundError(AppError):
    """租户不存在时抛出。"""

    def __init__(self, tenant_id: Optional[str] = None):
        message = f"租户不存在: {tenant_id}" if tenant_id else "租户不存在"
        super().__init__(message=message, code="TENANT_NOT_FOUND", status_code=404)
        self.tenant_id = tenant_id


class AuthenticationError(AppError):
    """认证失败时抛出。"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR", status_code=401)


class ValidationError(AppError):
    """输入校验失败时抛出。"""

    def __init__(self, message: str = "参数校验失败"):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=400)
