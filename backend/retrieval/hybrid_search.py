"""稠密+稀疏多路召回融合."""

from typing import Any, Optional

from config.constants import DEFAULT_TOP_K, HYBRID_PREFETCH_LIMIT
from config.settings import get_settings
from core.llm_factory import get_embedding
from core.sparse_encoder import SparseEncoder
from retrieval.base_retriever import BaseRetriever
from retrieval.bm25_retriever import BM25Retriever
from storage.vector_store import VectorStore


class HybridSearch:
    """融合稠密与稀疏检索结果（Qdrant RRF）。"""

    def __init__(
        self,
        tenant_id: str,
        vector_store: Optional[VectorStore] = None,
        sparse_encoder: Optional[SparseEncoder] = None,
    ):
        self.tenant_id = tenant_id
        settings = get_settings()
        self._vector_store = vector_store or VectorStore(tenant_id, settings)
        self._sparse_encoder = sparse_encoder or SparseEncoder()
        self._embedding = get_embedding()
        self.dense = BaseRetriever(tenant_id, self._vector_store)
        self.sparse = BM25Retriever(tenant_id, self._vector_store, self._sparse_encoder)

    def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """执行混合检索并融合结果。"""
        dense_vector = self._embedding.embed_query(query)
        sparse_vector = self._sparse_encoder.encode(query)
        return self._vector_store.hybrid_search(
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            top_k=top_k,
            filters=filters,
            prefetch_limit=max(top_k * 2, HYBRID_PREFETCH_LIMIT),
        )
