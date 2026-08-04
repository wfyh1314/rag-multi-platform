"""流式问答、会话管理、历史记录接口."""

import json
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from api.schemas import (
    AgentChatRequest,
    ChatStreamRequest,
    HistoryClearRequest,
    SessionCreateRequest,
    SessionImportRequest,
    SessionUpdateRequest,
)
from agent.rag_graph import build_rag_graph
from audit.chat_audit_service import ChatAuditService
from audit.content_risk import ContentRiskService
from chat.history_service import HistoryService
from chat.session_service import SessionService
from chat.sse_stream import format_sse_event, stream_agent_answer, stream_rag_answer
from core.logger import get_logger
from core.response import success
from core.security import get_current_user

router = APIRouter()
session_service = SessionService()
history_service = HistoryService()
content_risk = ContentRiskService()
chat_audit_service = ChatAuditService()
logger = get_logger(__name__)

PERSIST_WARNING = "消息持久化失败，刷新页面后可能无法恢复本次对话"


def _persist_assistant_message(
    *,
    user_id: str,
    session_id: str,
    query: str,
    answer: str,
    sources: list[dict[str, Any]] | None,
) -> str | None:
    """保存 assistant 消息与审计，失败时返回 warning 文案。"""
    try:
        history_service.save_message(
            session_id,
            role="assistant",
            content=answer,
            sources=sources,
            user_id=user_id,
        )
        chat_audit_service.log_chat(
            user_id=user_id,
            session_id=session_id,
            query=query,
            answer=answer,
            sources=sources,
        )
        return None
    except Exception as exc:
        logger.exception(
            "Failed to persist assistant message session_id=%s user_id=%s",
            session_id,
            user_id,
        )
        return PERSIST_WARNING


async def _persist_stream(
    stream_fn: AsyncGenerator[str, None],
    *,
    user_id: str,
    session_id: str | None,
    query: str,
) -> AsyncGenerator[str, None]:
    """包装 SSE 流：累积 assistant 回复并持久化消息与审计。"""
    assistant_parts: list[str] = []
    sources: list[dict[str, Any]] = []
    had_error = False

    async for event in stream_fn:
        if event.startswith("data: "):
            try:
                payload = json.loads(event[6:].strip())
                if "content" in payload:
                    assistant_parts.append(payload["content"])
                if "sources" in payload:
                    sources = payload["sources"]
                if "error" in payload:
                    had_error = True
                if payload.get("done") and session_id and not had_error:
                    answer = "".join(assistant_parts)
                    warning = _persist_assistant_message(
                        user_id=user_id,
                        session_id=session_id,
                        query=query,
                        answer=answer,
                        sources=sources or None,
                    )
                    if warning:
                        yield format_sse_event({"warning": warning})
            except json.JSONDecodeError:
                pass
        yield event


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

    user_id = current_user.get("user_id", current_user.get("id", ""))

    if body.session_id:
        try:
            history_service.save_message(
                body.session_id,
                role="user",
                content=body.query,
                user_id=user_id,
            )
        except Exception:
            logger.exception(
                "Failed to persist user message session_id=%s user_id=%s",
                body.session_id,
                user_id,
            )

    inner = stream_rag_answer(
        body.query,
        user=current_user,
        file_id=body.collection,
        tag_ids=body.tag_ids,
        history=body.history,
        **stream_kwargs,
    )

    stream_fn = _persist_stream(
        inner,
        user_id=user_id,
        session_id=body.session_id,
        query=body.query,
    )

    return StreamingResponse(
        stream_fn,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/history/clear", summary="清空会话历史（前端兼容）")
async def clear_history(
    body: HistoryClearRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """清空会话历史记录。"""
    history_service.clear(body.session_id, user_id=current_user.get("user_id", ""))
    return success(message="历史记录已清空")


# ---------- 会话管理 ----------

@router.post("/sessions", summary="创建会话")
async def create_session(
    body: SessionCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """创建聊天会话。"""
    result = session_service.create(current_user.get("user_id", ""), title=body.title)
    return success(result=result, message="创建成功")


@router.post("/sessions/import", summary="批量导入会话")
async def import_sessions(
    body: SessionImportRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """从 localStorage 等来源批量导入会话。"""
    imported = session_service.import_sessions(
        current_user.get("user_id", ""),
        body.sessions,
    )
    return success(result={"sessions": imported}, message="导入成功")


@router.get("/sessions", summary="会话列表")
async def list_sessions(
    include_archived: bool = Query(False, description="是否包含已归档会话"),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """获取用户会话列表。"""
    sessions = session_service.list_sessions(
        current_user.get("user_id", ""),
        include_archived=include_archived,
    )
    return success(result={"sessions": sessions}, message="获取成功")


@router.get("/sessions/{session_id}/history", summary="会话历史")
async def get_session_history(
    session_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """获取会话聊天历史。"""
    history = history_service.get_history(session_id, user_id=current_user.get("user_id", ""))
    return success(result={"history": history}, message="获取成功")


@router.put("/sessions/{session_id}", summary="更新会话")
async def update_session(
    session_id: str,
    body: SessionUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """重命名会话。"""
    result = session_service.rename(session_id, body.title, current_user.get("user_id", ""))
    return success(result=result, message="更新成功")


@router.delete("/sessions/{session_id}", summary="删除会话")
async def delete_session(
    session_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """删除会话及其消息。"""
    session_service.delete(session_id, current_user.get("user_id", ""))
    return success(message="删除成功")


@router.post("/sessions/{session_id}/archive", summary="归档会话")
async def archive_session(
    session_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """归档会话（从默认列表隐藏，可通过 include_archived 查看）。"""
    result = session_service.archive(session_id, current_user.get("user_id", ""))
    return success(result=result, message="归档成功")


@router.post("/chat/agent/stream", summary="LangGraph Agent 流式问答")
async def chat_agent_stream(
    body: AgentChatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> StreamingResponse:
    """Agent 检索 + SSE 流式生成。"""
    is_safe, matched = content_risk.check(body.query)
    if not is_safe:
        from chat.sse_stream import stream_error

        return StreamingResponse(
            stream_error(f"内容包含敏感词: {', '.join(matched)}"),
            media_type="text/event-stream",
        )

    user_id = current_user.get("user_id", "")
    if body.session_id:
        try:
            history_service.save_message(
                body.session_id, role="user", content=body.query, user_id=user_id
            )
        except Exception:
            logger.exception("Failed to persist user message session_id=%s", body.session_id)

    inner = stream_agent_answer(
        body.query,
        user=current_user,
        file_id=body.collection,
        tag_ids=body.tag_ids,
    )
    stream_fn = _persist_stream(
        inner,
        user_id=user_id,
        session_id=body.session_id,
        query=body.query,
    )
    return StreamingResponse(
        stream_fn,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/agent", summary="LangGraph Agent 问答")
async def chat_agent(
    body: AgentChatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """通过 LangGraph RAG 工作流返回答案。"""
    is_safe, matched = content_risk.check(body.query)
    if not is_safe:
        return success(
            result={
                "answer": f"内容包含敏感词: {', '.join(matched)}",
                "sources": [],
            },
            message="成功",
        )

    user_id = current_user.get("user_id", "")
    session_id = body.session_id or ""

    if session_id:
        try:
            history_service.save_message(
                session_id, role="user", content=body.query, user_id=user_id
            )
        except Exception:
            logger.exception("Failed to persist user message session_id=%s", session_id)

    graph = build_rag_graph()
    result = graph.invoke(
        {
            "query": body.query,
            "session_id": session_id,
            "user": current_user,
            "file_id": body.collection or "",
            "tag_ids": body.tag_ids or [],
        }
    )
    answer = result.get("answer", "")
    sources = result.get("sources", [])

    warning = None
    if session_id:
        warning = _persist_assistant_message(
            user_id=user_id,
            session_id=session_id,
            query=body.query,
            answer=answer,
            sources=sources,
        )

    response_result: dict[str, Any] = {"answer": answer, "sources": sources}
    if warning:
        response_result["warning"] = warning

    return success(result=response_result, message="成功")
