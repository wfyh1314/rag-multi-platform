"""Rerank 重排过滤噪声片段."""

from typing import Any

from config.constants import DEFAULT_RERANK_TOP_N


class RerankPipeline:
    """对检索结果重排，过滤噪声片段。"""

    def __init__(self, top_n: int = DEFAULT_RERANK_TOP_N):
        self.top_n = top_n

    def rerank(self, query: str, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """按与查询的相关性对文档重排。"""
        raise NotImplementedError
