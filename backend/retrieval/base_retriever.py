"""基础稠密向量检索（Qdrant 租户隔离空间）."""

from typing import Any, Optional

from config.settings import get_settings
from core.llm_factory import get_embedding
from storage.vector_store import VectorStore


class BaseRetriever:
    """基于 Qdrant 的稠密向量检索器。"""

    def __init__(self, tenant_id: str, vector_store: Optional[VectorStore] = None):
        self.tenant_id = tenant_id
        self._vector_store = vector_store or VectorStore(tenant_id, get_settings())
        self._embedding = get_embedding()

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """按稠密向量相似度检索文档。"""
        query_vector = self._embedding.embed_query(query)
        return self._vector_store.search_dense(query_vector, top_k=top_k, filters=filters)
