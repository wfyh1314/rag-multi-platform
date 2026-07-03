"""SSE 流式问答输出封装."""

import asyncio
import json
import queue
import threading
from typing import Any, AsyncGenerator, Optional

from chat.rag_service import build_rag_context
from core.llm_factory import get_llm


def format_sse_event(data: dict[str, Any]) -> str:
    """将字典格式化为 SSE data 行。"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _build_messages(
    query: str,
    history: Optional[list[dict[str, str]]] = None,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": "你是企业知识库问答助手，请用简洁准确的中文回答用户问题。"},
    ]
    if history:
        for item in history:
            role = item.get("role", "user")
            content = item.get("content", "")
            if content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": query})
    return messages


def _build_rag_messages(
    query: str,
    rag_context: str,
    history: Optional[list[dict[str, str]]] = None,
) -> list[dict[str, str]]:
    if rag_context:
        system_content = (
            "你是企业知识库问答助手。请优先依据以下检索到的参考片段回答用户问题；"
            "若片段不足以回答，请说明并基于常识补充。\n\n"
            f"{rag_context}"
        )
    else:
        system_content = (
            "你是企业知识库问答助手。知识库中未找到与用户问题相关的参考片段，"
            "请基于通用知识简洁准确作答，并说明未在知识库中找到依据。"
        )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
    if history:
        for item in history:
            role = item.get("role", "user")
            content = item.get("content", "")
            if content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": query})
    return messages


async def _stream_messages(
    messages: list[dict[str, str]],
    **llm_kwargs: Any,
) -> AsyncGenerator[str, None]:
    """通用 LLM 流式 SSE 输出。"""
    llm = get_llm()
    chunk_queue: queue.Queue = queue.Queue()
    errors: list[Exception] = []

    def _producer() -> None:
        try:
            for content in llm.stream(messages, **llm_kwargs):
                chunk_queue.put(content)
        except Exception as exc:
            errors.append(exc)
        finally:
            chunk_queue.put(None)

    threading.Thread(target=_producer, daemon=True).start()

    try:
        while True:
            content = await asyncio.to_thread(chunk_queue.get)
            if content is None:
                break
            yield format_sse_event({"content": content})

        if errors:
            yield format_sse_event({"error": str(errors[0])})
            return
        yield format_sse_event({"done": True})
    except Exception as exc:
        yield format_sse_event({"error": str(exc)})


async def stream_llm_answer(
    query: str,
    history: Optional[list[dict[str, str]]] = None,
    **llm_kwargs: Any,
) -> AsyncGenerator[str, None]:
    """调用通义 LLM 流式生成 SSE 事件."""
    messages = _build_messages(query, history)
    async for event in _stream_messages(messages, **llm_kwargs):
        yield event


async def stream_rag_answer(
    query: str,
    tenant_id: str,
    collection: Optional[str] = None,
    history: Optional[list[dict[str, str]]] = None,
    **llm_kwargs: Any,
) -> AsyncGenerator[str, None]:
    """混合检索后流式 RAG 问答。"""
    rag_context, _ = build_rag_context(tenant_id, query, collection=collection)
    messages = _build_rag_messages(query, rag_context, history)
    async for event in _stream_messages(messages, **llm_kwargs):
        yield event


async def stream_error(error: str) -> AsyncGenerator[str, None]:
    """输出 SSE 错误事件。"""
    yield format_sse_event({"error": error})


def build_chat_params(
    query: str,
    session_id: Optional[str] = None,
    collection: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """构建标准化的聊天请求参数。"""
    return {
        "query": query,
        "session_id": session_id,
        "collection": collection,
        "model": model,
        **kwargs,
    }
