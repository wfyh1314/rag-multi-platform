"""RAG 上下文构建测试."""

from unittest.mock import MagicMock, patch

from chat.rag_service import build_rag_context
from config.constants import DEFAULT_RERANK_TOP_N


def test_build_rag_context_applies_multimodal_search():
    user = {"user_id": "user-1"}
    hits = [
        {"id": "3", "content": "chunk three", "rerank_score": 0.9},
        {"id": "1", "content": "chunk one", "rerank_score": 0.8},
    ]

    with patch("chat.rag_service.get_accessible_file_record"), patch(
        "chat.rag_service.MultimodalRetrieval"
    ) as mock_mm_cls:
        mock_mm_cls.return_value.search = MagicMock(return_value=hits)

        context, result_hits = build_rag_context(user, "what is rag?", file_id="file-1")

    mock_mm_cls.return_value.search.assert_called_once_with(
        "what is rag?",
        top_k=DEFAULT_RERANK_TOP_N,
        filters={"file_id": "file-1"},
    )
    assert "chunk three" in context
    assert "chunk one" in context
    assert len(result_hits) == 2
    assert result_hits[0]["rerank_score"] == 0.9


def test_build_rag_context_returns_empty_when_no_hits():
    with patch("chat.rag_service._accessible_file_ids", return_value={"f1"}), patch(
        "chat.rag_service.MultimodalRetrieval"
    ) as mock_mm_cls:
        mock_mm_cls.return_value.search.return_value = []
        context, hits = build_rag_context({"user_id": "u1"}, "hello")

    assert context == ""
    assert hits == []


def test_build_rag_context_without_file_id_scopes_accessible_files():
    user = {"user_id": "user-1"}
    hits = [{"id": "1", "content": "chunk one", "rerank_score": 0.8}]

    with patch("chat.rag_service._accessible_file_ids", return_value={"f1", "f2"}), patch(
        "chat.rag_service.MultimodalRetrieval"
    ) as mock_mm_cls:
        mock_mm_cls.return_value.search = MagicMock(return_value=hits)
        context, result_hits = build_rag_context(user, "what is rag?")

    mock_mm_cls.return_value.search.assert_called_once_with(
        "what is rag?",
        top_k=DEFAULT_RERANK_TOP_N,
        filters={"_should": [{"file_id": "f1"}, {"file_id": "f2"}]},
    )
    assert "chunk one" in context
    assert len(result_hits) == 1


def test_build_rag_context_without_file_id_returns_empty_when_no_accessible():
    with patch("chat.rag_service._accessible_file_ids", return_value=set()), patch(
        "chat.rag_service.MultimodalRetrieval"
    ) as mock_mm_cls:
        context, hits = build_rag_context({"user_id": "u1"}, "hello")

    mock_mm_cls.return_value.search.assert_not_called()
    assert context == ""
    assert hits == []
