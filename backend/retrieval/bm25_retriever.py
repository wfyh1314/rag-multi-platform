"""BM25 风格稀疏向量检索（Qdrant sparse）."""

from typing import Any, Optional

from config.settings import get_settings
from core.sparse_encoder import SparseEncoder
from storage.vector_store import VectorStore


class BM25Retriever:
    """基于 Qdrant sparse 向量的关键词检索。"""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        sparse_encoder: Optional[SparseEncoder] = None,
    ):
        self._vector_store = vector_store or VectorStore(get_settings())
        self._sparse_encoder = sparse_encoder or SparseEncoder()

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """按稀疏向量检索文档。"""
        sparse_vector = self._sparse_encoder.encode(query)
        return self._vector_store.search_sparse(sparse_vector, top_k=top_k, filters=filters)
