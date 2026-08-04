"""Rerank 重排过滤噪声片段."""

import logging
from typing import Any

from config.constants import DEFAULT_RERANK_TOP_N
from core.llm_factory import get_reranker

logger = logging.getLogger(__name__)


class RerankPipeline:
    """对检索结果重排，过滤噪声片段。"""

    def __init__(self, top_n: int = DEFAULT_RERANK_TOP_N):
        self.top_n = top_n

    def rerank(self, query: str, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """按与查询的相关性对文档重排。"""
        if not documents:
            return []

        top_n = min(self.top_n, len(documents))
        texts = [doc.get("content", "") for doc in documents]

        try:
            results = get_reranker().rerank(query, texts, top_n=top_n)
        except Exception as exc:
            logger.warning("Rerank failed, fallback to hybrid order: %s", exc)
            return documents[:top_n]

        if not results:
            logger.warning("Rerank returned empty results, fallback to hybrid order")
            return documents[:top_n]

        reranked: list[dict[str, Any]] = []
        for item in results:
            idx = item.get("index")
            if idx is None or idx < 0 or idx >= len(documents):
                continue
            hit = documents[idx].copy()
            hit["rerank_score"] = item.get("relevance_score", 0.0)
            reranked.append(hit)

        if not reranked:
            return documents[:top_n]

        return reranked
