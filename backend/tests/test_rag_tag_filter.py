"""RAG 标签过滤测试."""

from unittest.mock import MagicMock, patch

from chat.rag_service import build_rag_context


def test_build_rag_context_with_tag_ids_uses_file_id_prefilter():
    user = {"user_id": "user-1"}
    hits = [{"id": "1", "content": "tagged chunk", "metadata": {"file_id": "f1"}}]

    with patch("chat.rag_service._accessible_file_ids", return_value={"f1", "f2"}), patch(
        "chat.rag_service.get_db_session"
    ) as mock_db, patch("chat.rag_service.MultimodalRetrieval") as mock_mm_cls:
        repo = MagicMock()
        repo.list_file_ids_by_tag_ids.return_value = {"f1"}
        mock_db.return_value.__enter__.return_value = MagicMock()
        with patch("chat.rag_service.FileTagRepository", return_value=repo):
            mock_mm_cls.return_value.search = MagicMock(return_value=hits)

            context, result_hits = build_rag_context(user, "query", tag_ids=["tag-1", "tag-2"])

    mock_mm_cls.return_value.search.assert_called_once()
    filters = mock_mm_cls.return_value.search.call_args.kwargs["filters"]
    assert filters == {"file_id": "f1"}
    assert "tag_ids" not in filters
    assert "tagged chunk" in context
    assert len(result_hits) == 1


def test_build_rag_context_with_tag_ids_no_match_returns_empty():
    user = {"user_id": "user-1"}

    with patch("chat.rag_service._accessible_file_ids", return_value={"f1"}), patch(
        "chat.rag_service.get_db_session"
    ) as mock_db, patch("chat.rag_service.MultimodalRetrieval") as mock_mm_cls:
        repo = MagicMock()
        repo.list_file_ids_by_tag_ids.return_value = set()
        mock_db.return_value.__enter__.return_value = MagicMock()
        with patch("chat.rag_service.FileTagRepository", return_value=repo):
            context, hits = build_rag_context(user, "query", tag_ids=["tag-1"])

    mock_mm_cls.return_value.search.assert_not_called()
    assert context == ""
    assert hits == []
