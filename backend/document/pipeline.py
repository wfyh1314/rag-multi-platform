"""文档处理流水线：加载 → 清洗 → 分块 → 向量化 → 入库."""

from typing import Any, Optional

from config.settings import Settings, get_settings
from core.llm_factory import get_embedding
from core.sparse_encoder import SparseEncoder
from document.chunkers.splitter import split_document
from document.cleaners.cleaner import clean_document
from document.loaders import load_document
from storage.vector_store import VectorStore


class DocumentProcessor:
    """端到端文档入库流水线。"""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        embedding_client: Optional[Any] = None,
        vector_store_cls: type[VectorStore] = VectorStore,
    ):
        self.settings = settings or get_settings()
        self._embedding_client = embedding_client
        self._vector_store_cls = vector_store_cls
        self._sparse_encoder = SparseEncoder()

    # 向量化客户端
    @property
    def embedding(self) -> Any:
        if self._embedding_client is None:
            self._embedding_client = get_embedding(self.settings)
        return self._embedding_client

    def process(
        self,
        file_path: str,
        file_id: str,
        user_id: str,
        visibility: str,
        tag_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """执行完整流水线：加载 → 清洗 → 分块 → 向量化 → 入库。"""
        # 1. 加载
        raw_chunks = load_document(file_path)
        dict_chunks = [{"content": c.content, **c.metadata} for c in raw_chunks]

        # 2. 清洗
        cleaned = clean_document(dict_chunks)

        # 3. 分块
        split_chunks = split_document(
            cleaned,
            strategy=self.settings.chunk_strategy,
            chunk_size=self.settings.chunk_size,
            overlap=self.settings.chunk_overlap,
            breakpoint_threshold=self.settings.semantic_chunk_breakpoint_threshold,
        )

        if not split_chunks:
            return {
                "file_id": file_id,
                "chunk_count": 0,
                "status": "indexed",
                "message": "文档无有效内容块",
            }

        # 附加租户/文件元数据
        for i, chunk in enumerate(split_chunks):
            chunk["chunk_index"] = i
            chunk["file_id"] = file_id
            chunk["user_id"] = user_id
            chunk["owner_id"] = user_id
            chunk["visibility"] = visibility
            file_type = chunk.get("file_type", "")
            chunk["modality"] = "image" if file_type == "image" else "text"
            if chunk.get("source"):
                chunk["media_path"] = chunk.get("source")
            if tag_ids:
                chunk["tag_ids"] = tag_ids

        # 4. 向量化（稠密 + 稀疏）
        texts = [c["content"] for c in split_chunks]
        dense_vectors = self.embedding.embed_documents(texts)
        sparse_vectors = self._sparse_encoder.encode_batch(texts)

        # 5. 写入 Qdrant
        vector_store = self._vector_store_cls(self.settings)
        vector_size = len(dense_vectors[0]) if dense_vectors else self.settings.embedding_dimension
        vector_store.ensure_collection(vector_size)

        points = []
        for i, (chunk, dense_vector, sparse_vector) in enumerate(
            zip(split_chunks, dense_vectors, sparse_vectors)
        ):
            point_id = f"{file_id}_{i}"
            meta = {k: v for k, v in chunk.items() if k != "content"}
            points.append({
                "id": point_id,
                "dense_vector": dense_vector,
                "sparse_vector": sparse_vector,
                "content": chunk["content"],
                "metadata": meta,
            })
        vector_store.upsert(points)

        return {
            "file_id": file_id,
            "chunk_count": len(split_chunks),
            "status": "indexed",
            "message": f"成功索引 {len(split_chunks)} 个文本块",
        }
