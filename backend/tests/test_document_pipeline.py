"""DocumentProcessor 流水线测试."""

import pytest
from qdrant_client.models import SparseVector

from document.pipeline import DocumentProcessor


class MockEmbedding:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class MockVectorStore:
    instances: list["MockVectorStore"] = []

    def __init__(self, tenant_id: str, settings=None):
        self.tenant_id = tenant_id
        self.upserted: list[dict] = []
        MockVectorStore.instances.append(self)

    def ensure_collection(self, vector_size: int) -> None:
        pass

    def upsert(self, points: list[dict]) -> None:
        self.upserted.extend(points)


@pytest.fixture
def mock_pipeline():
    MockVectorStore.instances.clear()
    processor = DocumentProcessor(
        embedding_client=MockEmbedding(),
        vector_store_cls=MockVectorStore,
    )
    return processor


def test_pipeline_full_flow(tmp_path, mock_pipeline):
    """流水线应完成加载、清洗、分块、向量化与入库。"""
    file_path = tmp_path / "doc.txt"
    file_path.write_text("Hello world. " * 50, encoding="utf-8")

    result = mock_pipeline.process(
        file_path=str(file_path),
        tenant_id="tenant-1",
        file_id="file-abc",
        user_id="user-1",
    )

    assert result["status"] == "indexed"
    assert result["chunk_count"] > 0
    assert result["file_id"] == "file-abc"

    store = MockVectorStore.instances[0]
    assert len(store.upserted) == result["chunk_count"]
    assert store.upserted[0]["content"]
    assert len(store.upserted[0]["dense_vector"]) == 3
    assert isinstance(store.upserted[0]["sparse_vector"], SparseVector)


def test_pipeline_empty_content(tmp_path, mock_pipeline):
    """清洗后无有效内容的文档应返回零块。"""
    file_path = tmp_path / "empty.txt"
    file_path.write_text("   ", encoding="utf-8")

    with pytest.raises(Exception):
        mock_pipeline.process(
            file_path=str(file_path),
            tenant_id="tenant-1",
            file_id="file-empty",
            user_id="user-1",
        )
