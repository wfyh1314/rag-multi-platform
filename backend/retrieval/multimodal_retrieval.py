"""图文联合检索，图片/文本统一向量空间."""

from typing import Any, Optional

from config.constants import DEFAULT_RERANK_TOP_N, HYBRID_PREFETCH_LIMIT
from retrieval.hybrid_search import HybridSearch
from retrieval.rerank_pipeline import RerankPipeline


def merge_filters(
    base: Optional[dict[str, Any]],
    extra: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """合并 Qdrant 过滤条件，支持 _should 与 modality 组合。"""
    if not base:
        return extra
    if not extra:
        return base
    if base.get("_should"):
        return {
            "_should": [{**group, **extra} for group in base["_should"]],
        }
    return {**base, **extra}


class MultimodalRetrieval:
    """图文统一向量空间的多模态检索。"""

    def search(
        self,
        query: str,
        top_k: int = 10,
        modality: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """在统一向量空间中检索文本与图片。"""
        search_filters: dict[str, Any] | None = filters
        if modality in {"text", "image"}:
            search_filters = merge_filters(filters, {"modality": modality})

        text_hits = HybridSearch().search(
            query, top_k=HYBRID_PREFETCH_LIMIT, filters=search_filters
        )

        if modality is None:
            image_filters = merge_filters(filters, {"modality": "image"})
            image_hits = HybridSearch().search(
                query, top_k=HYBRID_PREFETCH_LIMIT, filters=image_filters
            )
            merged: dict[str, dict[str, Any]] = {}
            for hit in text_hits + image_hits:
                hit_id = hit.get("id", "")
                if hit_id not in merged or hit.get("score", 0) > merged[hit_id].get("score", 0):
                    merged[hit_id] = hit
            hits = sorted(merged.values(), key=lambda h: h.get("score", 0), reverse=True)
        else:
            hits = text_hits

        if not hits:
            return []
        rerank_n = min(top_k, DEFAULT_RERANK_TOP_N)
        return RerankPipeline(top_n=rerank_n).rerank(query, hits[:HYBRID_PREFETCH_LIMIT])
