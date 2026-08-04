"""标准问答工作流：提问 → 检索 → 生成答案."""

from typing import Any

from langgraph.graph import END, StateGraph

from agent.state_schema import RAGState
from agent.tools import retrieval_tool
from chat.rag_service import format_rag_context, hits_to_sources
from core.llm_factory import get_llm


def _retrieve_node(state: RAGState) -> dict[str, Any]:
    query = state.get("query", "")
    user = state.get("user") or {}
    file_id = state.get("file_id") or None
    tag_ids = state.get("tag_ids") or None
    hits = retrieval_tool(
        query,
        top_k=10,
        user=user if user else None,
        file_id=file_id,
        tag_ids=tag_ids,
    )
    documents = hits_to_sources(hits)
    return {"documents": documents, "sources": documents}


def _generate_node(state: RAGState) -> dict[str, Any]:
    query = state.get("query", "")
    documents = state.get("documents") or []
    hits = [
        {
            "id": doc.get("doc_id"),
            "content": doc.get("content", ""),
            "metadata": doc.get("metadata", {}),
            "score": doc.get("score"),
        }
        for doc in documents
    ]
    context = format_rag_context(hits)
    if context:
        system = (
            "你是企业知识库问答助手。请依据以下检索片段回答问题。\n\n"
            f"{context}"
        )
    else:
        system = "你是企业知识库问答助手。知识库未找到相关内容，请基于常识作答并说明无依据。"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]
    llm = get_llm()
    response = llm.invoke(messages)
    answer = response.content if hasattr(response, "content") else str(response)
    return {
        "answer": answer,
        "messages": [{"role": "assistant", "content": answer}],
    }


def build_rag_graph() -> Any:
    """构建 LangGraph RAG 工作流图。"""
    graph = StateGraph(RAGState)
    graph.add_node("retrieve", _retrieve_node)
    graph.add_node("generate", _generate_node)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()
