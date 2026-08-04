"""内置检索工具，无复杂工具审查."""

from typing import Any, Optional

from chat.rag_service import search_rag_hits


def retrieval_tool(
    query: str,
    top_k: int = 10,
    user: Optional[dict[str, Any]] = None,
    file_id: Optional[str] = None,
    tag_ids: Optional[list[str]] = None,
    filters: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """LangGraph Agent 内置检索工具（复用主 RAG 多模态检索链）。"""
    if user is not None:
        return search_rag_hits(user, query, file_id, tag_ids, top_k=top_k)
    # 兼容无 user 的旧调用（测试或内部）
    from config.constants import DEFAULT_RERANK_TOP_N, HYBRID_PREFETCH_LIMIT
    from retrieval.multimodal_retrieval import MultimodalRetrieval
    from retrieval.rerank_pipeline import RerankPipeline

    hits = MultimodalRetrieval().search(
        query, top_k=HYBRID_PREFETCH_LIMIT, filters=filters
    )
    if not hits:
        return []
    rerank_n = min(top_k, DEFAULT_RERANK_TOP_N)
    return RerankPipeline(top_n=rerank_n).rerank(query, hits)
