"""HybridSearch 单元测试."""

from qdrant_client.models import SparseVector

from retrieval.hybrid_search import HybridSearch


class MockEmbedding:
    def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class MockVectorStore:
    def __init__(self, settings=None):
        self.last_hybrid_args: dict | None = None

    def hybrid_search(self, dense_vector, sparse_vector, top_k, filters=None, prefetch_limit=20):
        self.last_hybrid_args = {
            "dense_vector": dense_vector,
            "sparse_vector": sparse_vector,
            "top_k": top_k,
            "filters": filters,
            "prefetch_limit": prefetch_limit,
        }
        return [
            {
                "id": "p1",
                "score": 0.9,
                "content": "检索片段",
                "metadata": {"file_id": "f1"},
            }
        ]


def test_hybrid_search_calls_vector_store(monkeypatch):
    store = MockVectorStore()
    search = HybridSearch(vector_store=store)
    search._embedding = MockEmbedding()

    results = search.search("测试问题", top_k=5, filters={"file_id": "f1"})

    assert len(results) == 1
    assert results[0]["content"] == "检索片段"
    assert store.last_hybrid_args is not None
    assert store.last_hybrid_args["top_k"] == 5
    assert store.last_hybrid_args["filters"] == {"file_id": "f1"}
    assert isinstance(store.last_hybrid_args["sparse_vector"], SparseVector)
