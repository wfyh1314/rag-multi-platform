"""对话 State 状态定义."""

from typing import Any, TypedDict

from core.reducers import DocumentsReducer, MessagesReducer


class RAGState(TypedDict, total=False):
    """RAG 问答工作流的 LangGraph 状态。"""

    tenant_id: str
    session_id: str
    query: str
    messages: MessagesReducer
    documents: DocumentsReducer
    answer: str
    sources: list[dict[str, Any]]
