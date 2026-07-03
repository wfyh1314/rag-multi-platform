"""审计日志、操作记录查询接口."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.schemas import AuditQueryRequest, PaginatedResponse
from audit.chat_audit_service import ChatAuditService
from audit.op_log_service import OpLogService
from core.security import get_current_user

router = APIRouter()
op_log_service = OpLogService()
chat_audit_service = ChatAuditService()


@router.get("/audit/operations", response_model=PaginatedResponse, summary="操作审计日志")
async def list_operation_logs(
    query: AuditQueryRequest = Depends(),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> PaginatedResponse:
    """查询操作审计日志（占位）。"""
    raise HTTPException(status_code=501, detail="操作审计查询接口待实现")


@router.get("/audit/chats", response_model=PaginatedResponse, summary="问答审计日志")
async def list_chat_audit_logs(
    query: AuditQueryRequest = Depends(),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> PaginatedResponse:
    """查询问答审计日志（占位）。"""
    raise HTTPException(status_code=501, detail="问答审计查询接口待实现")
