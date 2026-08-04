"""RerankPipeline 单元测试."""

from unittest.mock import MagicMock

import pytest

from retrieval.rerank_pipeline import RerankPipeline


def test_rerank_empty_documents():
    pipeline = RerankPipeline(top_n=5)
    assert pipeline.rerank("query", []) == []


def test_rerank_reorders_by_score(monkeypatch):
    mock_reranker = MagicMock()
    mock_reranker.rerank.return_value = [
        {"index": 2, "relevance_score": 0.95},
        {"index": 0, "relevance_score": 0.80},
    ]
    monkeypatch.setattr("retrieval.rerank_pipeline.get_reranker", lambda: mock_reranker)

    documents = [
        {"id": "a", "content": "first chunk"},
        {"id": "b", "content": "second chunk"},
        {"id": "c", "content": "third chunk"},
    ]
    pipeline = RerankPipeline(top_n=2)
    result = pipeline.rerank("test query", documents)

    assert len(result) == 2
    assert result[0]["id"] == "c"
    assert result[0]["rerank_score"] == 0.95
    assert result[1]["id"] == "a"
    assert result[1]["rerank_score"] == 0.80
    mock_reranker.rerank.assert_called_once_with(
        "test query",
        ["first chunk", "second chunk", "third chunk"],
        top_n=2,
    )


def test_rerank_fallback_on_api_error(monkeypatch):
    mock_reranker = MagicMock()
    mock_reranker.rerank.side_effect = RuntimeError("API unavailable")
    monkeypatch.setattr("retrieval.rerank_pipeline.get_reranker", lambda: mock_reranker)

    documents = [
        {"id": "a", "content": "first"},
        {"id": "b", "content": "second"},
        {"id": "c", "content": "third"},
    ]
    pipeline = RerankPipeline(top_n=2)
    result = pipeline.rerank("query", documents)

    assert result == documents[:2]


def test_rerank_fallback_on_empty_results(monkeypatch):
    mock_reranker = MagicMock()
    mock_reranker.rerank.return_value = []
    monkeypatch.setattr("retrieval.rerank_pipeline.get_reranker", lambda: mock_reranker)

    documents = [{"id": "a", "content": "only one"}]
    pipeline = RerankPipeline(top_n=5)
    result = pipeline.rerank("query", documents)

    assert result == documents
