"""审计日志、操作记录查询接口."""

from typing import Any

from fastapi import APIRouter, Depends

from api.schemas import AuditQueryRequest, PaginatedResponse
from audit.chat_audit_service import ChatAuditService
from audit.op_log_service import OpLogService
from core.response import success
from core.security import get_current_user

router = APIRouter()
op_log_service = OpLogService()
chat_audit_service = ChatAuditService()


@router.get("/audit/operations", summary="操作审计日志")
async def list_operation_logs(
    query: AuditQueryRequest = Depends(),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """查询操作审计日志。"""
    result = op_log_service.query(
        action=query.action,
        user_id=query.user_id or current_user.get("user_id"),
        page=query.page,
        page_size=query.page_size,
    )
    return success(result=result, message="获取成功")


@router.get("/audit/chats", summary="问答审计日志")
async def list_chat_audit_logs(
    query: AuditQueryRequest = Depends(),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """查询问答审计日志。"""
    result = chat_audit_service.query(
        user_id=query.user_id or current_user.get("user_id"),
        session_id=query.session_id,
        page=query.page,
        page_size=query.page_size,
    )
    return success(result=result, message="获取成功")
