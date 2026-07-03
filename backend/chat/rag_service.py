"""RAG 检索上下文构建."""

from typing import Any, Optional

from config.constants import DEFAULT_TOP_K
from file_mgr.file_service import get_file_id_by_filename
from retrieval.hybrid_search import HybridSearch


def build_rag_context(
    tenant_id: str,
    query: str,
    collection: Optional[str] = None,
    top_k: int = DEFAULT_TOP_K,
) -> tuple[str, list[dict[str, Any]]]:
    """混合检索并格式化为 LLM 上下文。

    Returns:
        (context_text, hits) — context_text 为空表示未命中。
    """
    filters: dict[str, Any] | None = None
    if collection:
        file_id = get_file_id_by_filename(tenant_id, collection)
        if file_id:
            filters = {"file_id": file_id}

    hits = HybridSearch(tenant_id).search(query, top_k=top_k, filters=filters)
    if not hits:
        return "", []

    parts: list[str] = []
    for i, hit in enumerate(hits, start=1):
        content = hit.get("content", "").strip()
        if content:
            parts.append(f"[{i}] {content}")

    if not parts:
        return "", hits

    context = "以下是从知识库检索到的参考片段：\n\n" + "\n\n".join(parts)
    return context, hits
