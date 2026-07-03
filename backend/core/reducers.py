"""LangGraph State 归约器（轻量基础问答 Agent）."""

from operator import add
from typing import Annotated, Any


def merge_messages(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """合并 LangGraph 状态中的消息列表。"""
    return left + right


def merge_documents(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """合并检索文档列表，按 doc_id 去重。"""
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for doc in left + right:
        doc_id = doc.get("doc_id") or doc.get("id") or str(hash(doc.get("content", "")))
        if doc_id not in seen:
            seen.add(doc_id)
            merged.append(doc)
    return merged


def append_strings(left: str, right: str) -> str:
    """拼接字符串，用于流式答案累积。"""
    return left + right


# LangGraph 状态字段的 Annotated 归约器
MessagesReducer = Annotated[list[dict[str, Any]], add]
DocumentsReducer = Annotated[list[dict[str, Any]], merge_documents]
