"""统一 API 响应封装."""

from typing import Any, Optional

from pydantic import BaseModel

from config.response_codes import (
    BAD_REQUEST,
    FORBIDDEN,
    INTERNAL_ERROR,
    NOT_FOUND,
    NOT_IMPLEMENTED,
    SUCCESS,
    UNAUTHORIZED,
)
from core.request_context import get_request_uuid


class ApiResponse(BaseModel):
    """统一响应体。"""

    code: int
    description: str = ""
    message: str = ""
    result: Any | None = None
    uuid: str = ""


def build_response(
    code: int,
    message: str = "",
    description: str = "",
    result: Any | None = None,
    request_uuid: Optional[str] = None,
) -> dict[str, Any]:
    """构建统一响应字典。"""
    return ApiResponse(
        code=code,
        description=description,
        message=message,
        result=result,
        uuid=request_uuid if request_uuid is not None else get_request_uuid(),
    ).model_dump()


def success(
    result: Any | None = None,
    message: str = "操作成功",
    description: str = "",
    request_uuid: Optional[str] = None,
) -> dict[str, Any]:
    """成功响应。"""
    return build_response(
        code=SUCCESS,
        message=message,
        description=description,
        result=result,
        request_uuid=request_uuid,
    )


def fail(
    code: int,
    message: str,
    description: str = "",
    result: Any | None = None,
    request_uuid: Optional[str] = None,
) -> dict[str, Any]:
    """失败响应。"""
    return build_response(
        code=code,
        message=message,
        description=description,
        result=result,
        request_uuid=request_uuid,
    )


def fail_from_http_status(
    status_code: int,
    message: str,
    description: str = "",
    result: Any | None = None,
    request_uuid: Optional[str] = None,
) -> dict[str, Any]:
    """根据 HTTP 状态码映射业务码。"""
    code_map = {
        400: BAD_REQUEST,
        401: UNAUTHORIZED,
        403: FORBIDDEN,
        404: NOT_FOUND,
        422: BAD_REQUEST,
        501: NOT_IMPLEMENTED,
    }
    return fail(
        code=code_map.get(status_code, INTERNAL_ERROR),
        message=message,
        description=description,
        result=result,
        request_uuid=request_uuid,
    )
