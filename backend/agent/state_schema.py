"""对话 State 状态定义."""

from typing import Any, TypedDict

from core.reducers import DocumentsReducer, MessagesReducer


class RAGState(TypedDict, total=False):
    """RAG 问答工作流的 LangGraph 状态。"""

    session_id: str
    query: str
    user: dict[str, Any]
    file_id: str
    tag_ids: list[str]
    messages: MessagesReducer
    documents: DocumentsReducer
    answer: str
    sources: list[dict[str, Any]]
