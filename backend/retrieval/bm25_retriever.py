"""Qdrant 稀疏全文检索（BM25 风格），支持关键词匹配."""

from typing import Any, Optional

from config.settings import get_settings
from core.sparse_encoder import SparseEncoder
from storage.vector_store import VectorStore


class BM25Retriever:
    """基于 Qdrant 稀疏向量的关键词检索器。"""

    def __init__(
        self,
        tenant_id: str,
        vector_store: Optional[VectorStore] = None,
        sparse_encoder: Optional[SparseEncoder] = None,
    ):
        self.tenant_id = tenant_id
        self._vector_store = vector_store or VectorStore(tenant_id, get_settings())
        self._sparse_encoder = sparse_encoder or SparseEncoder()

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """通过稀疏向量关键词匹配检索文档。"""
        sparse_vector = self._sparse_encoder.encode(query)
        return self._vector_store.search_sparse(sparse_vector, top_k=top_k, filters=filters)
