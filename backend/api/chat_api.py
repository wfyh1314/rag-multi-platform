"""流式问答、会话管理、历史记录接口."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.schemas import (
    ChatStreamRequest,
    HistoryClearRequest,
    MessageResponse,
    SessionCreateRequest,
    SessionResponse,
)
from audit.content_risk import ContentRiskService
from chat.history_service import HistoryService
from chat.session_service import SessionService
from chat.sse_stream import stream_llm_answer, stream_rag_answer
from core.security import get_current_user

router = APIRouter()
session_service = SessionService()
history_service = HistoryService()
content_risk = ContentRiskService()


# ---------- 前端兼容路由 ----------

@router.post("/chat/stream", summary="SSE 流式问答（前端兼容）")
async def chat_stream(
    body: ChatStreamRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> StreamingResponse:
    """通过 SSE 流式返回问答内容。"""
    is_safe, matched = content_risk.check(body.query)
    if not is_safe:
        from chat.sse_stream import stream_error
        return StreamingResponse(
            stream_error(f"内容包含敏感词: {', '.join(matched)}"),
            media_type="text/event-stream",
        )

    stream_kwargs: dict[str, Any] = {}
    if body.model:
        stream_kwargs["model"] = body.model
    if body.temperature is not None:
        stream_kwargs["temperature"] = body.temperature
    if body.max_length is not None:
        stream_kwargs["max_tokens"] = body.max_length

    tenant_id = current_user.get("tenant_id", "dev-tenant")
    if body.collection:
        stream_fn = stream_rag_answer(
            body.query,
            tenant_id=tenant_id,
            collection=body.collection,
            history=body.history,
            **stream_kwargs,
        )
    else:
        stream_fn = stream_llm_answer(body.query, history=body.history, **stream_kwargs)

    return StreamingResponse(
        stream_fn,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/history/clear", response_model=MessageResponse, summary="清空会话历史（前端兼容）")
async def clear_history(
    body: HistoryClearRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> MessageResponse:
    """清空会话历史记录。"""
    history_service.clear(body.session_id)
    return MessageResponse(message="历史记录已清空")


# ---------- 会话管理 ----------

@router.post("/sessions", response_model=SessionResponse, summary="创建会话")
async def create_session(
    body: SessionCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> SessionResponse:
    """创建聊天会话（占位）。"""
    raise HTTPException(status_code=501, detail="会话创建接口待实现")


@router.get("/sessions", summary="会话列表")
async def list_sessions(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, list]:
    """获取用户会话列表（占位）。"""
    return {"sessions": []}


@router.get("/sessions/{session_id}/history", summary="会话历史")
async def get_session_history(
    session_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, list]:
    """获取会话聊天历史（占位）。"""
    return {"history": []}
