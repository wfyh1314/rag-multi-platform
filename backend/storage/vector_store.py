"""Qdrant 封装：按租户创建独立集合、稠密+稀疏向量增删改查、混合检索."""

import uuid
from typing import Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchValue,
    Modifier,
    PointStruct,
    Prefetch,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from config.constants import (
    DENSE_VECTOR_NAME,
    HYBRID_PREFETCH_LIMIT,
    SPARSE_VECTOR_NAME,
)
from config.settings import Settings, get_settings
from core.exceptions import AppError


class VectorStore:
    """Qdrant 向量存储，按租户隔离集合，支持 dense + sparse 混合检索。"""

    def __init__(self, tenant_id: str, settings: Optional[Settings] = None):
        self.tenant_id = tenant_id
        cfg = settings or get_settings()
        self.collection_name = f"{cfg.qdrant_collection_prefix}{tenant_id}"
        self._client = QdrantClient(
            host=cfg.qdrant_host,
            port=cfg.qdrant_port,
            api_key=cfg.qdrant_api_key or None,
        )

    def ensure_collection(self, vector_size: int) -> None:
        """集合不存在时创建；已存在则校验 dense + sparse 命名向量 schema。"""
        collections = [c.name for c in self._client.get_collections().collections]
        if self.collection_name not in collections:
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    DENSE_VECTOR_NAME: VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE,
                    ),
                },
                sparse_vectors_config={
                    SPARSE_VECTOR_NAME: SparseVectorParams(modifier=Modifier.IDF),
                },
            )
            return

        info = self._client.get_collection(self.collection_name)
        params = info.config.params
        vectors = params.vectors
        sparse = params.sparse_vectors or {}

        has_dense = isinstance(vectors, dict) and DENSE_VECTOR_NAME in vectors
        has_sparse = SPARSE_VECTOR_NAME in sparse

        if not (has_dense and has_sparse):
            raise AppError(
                f"集合 {self.collection_name} 为旧版单向量 schema，"
                f"请删除该 collection 后重新上传文档。",
                code="QDRANT_SCHEMA_MISMATCH",
                status_code=409,
            )

    def upsert(self, points: list[dict[str, Any]]) -> None:
        """写入或更新向量点。

        每个点字典格式：{id, dense_vector, sparse_vector, content, metadata}
        """
        if not points:
            return

        qdrant_points = []
        for p in points:
            point_id = p.get("id") or str(uuid.uuid4())
            payload = {"content": p["content"], **(p.get("metadata") or {})}
            qdrant_points.append(
                PointStruct(
                    id=self._to_point_id(point_id),
                    vector={
                        DENSE_VECTOR_NAME: p["dense_vector"],
                        SPARSE_VECTOR_NAME: p["sparse_vector"],
                    },
                    payload=payload,
                )
            )
        self._client.upsert(collection_name=self.collection_name, points=qdrant_points)

    def search_dense(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """稠密向量相似度检索。"""
        return self._query_to_results(
            query=query_vector,
            using=DENSE_VECTOR_NAME,
            top_k=top_k,
            filters=filters,
        )

    def search_sparse(
        self,
        sparse_vector: SparseVector,
        top_k: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """稀疏向量关键词检索。"""
        return self._query_to_results(
            query=sparse_vector,
            using=SPARSE_VECTOR_NAME,
            top_k=top_k,
            filters=filters,
        )

    def hybrid_search(
        self,
        dense_vector: list[float],
        sparse_vector: SparseVector,
        top_k: int = 10,
        filters: Optional[dict[str, Any]] = None,
        prefetch_limit: int = HYBRID_PREFETCH_LIMIT,
    ) -> list[dict[str, Any]]:
        """RRF 融合稠密与稀疏检索结果。"""
        qdrant_filter = self._build_filter(filters) if filters else None
        response = self._client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                Prefetch(
                    query=dense_vector,
                    using=DENSE_VECTOR_NAME,
                    limit=prefetch_limit,
                    filter=qdrant_filter,
                ),
                Prefetch(
                    query=sparse_vector,
                    using=SPARSE_VECTOR_NAME,
                    limit=prefetch_limit,
                    filter=qdrant_filter,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return [self._hit_to_dict(hit) for hit in response.points]

    def delete(self, point_ids: list[str]) -> None:
        """按 ID 删除向量。"""
        if not point_ids:
            return
        self._client.delete(
            collection_name=self.collection_name,
            points_selector=[self._to_point_id(pid) for pid in point_ids],
        )

    def _query_to_results(
        self,
        query: Any,
        using: str,
        top_k: int,
        filters: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        qdrant_filter = self._build_filter(filters) if filters else None
        response = self._client.query_points(
            collection_name=self.collection_name,
            query=query,
            using=using,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return [self._hit_to_dict(hit) for hit in response.points]

    @staticmethod
    def _hit_to_dict(hit: Any) -> dict[str, Any]:
        payload = hit.payload or {}
        return {
            "id": str(hit.id),
            "score": hit.score,
            "content": payload.get("content", ""),
            "metadata": {k: v for k, v in payload.items() if k != "content"},
        }

    def _build_filter(self, filters: dict[str, Any]) -> Filter:
        conditions = [
            FieldCondition(key=key, match=MatchValue(value=value))
            for key, value in filters.items()
        ]
        return Filter(must=conditions)

    @staticmethod
    def _to_point_id(point_id: str) -> str:
        """将字符串 ID 转换为 Qdrant 所需的 UUID 格式。"""
        try:
            uuid.UUID(str(point_id))
            return str(point_id)
        except ValueError:
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(point_id)))
