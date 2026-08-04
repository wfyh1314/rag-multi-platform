"""多模态检索测试."""

from unittest.mock import MagicMock, patch

from retrieval.multimodal_retrieval import MultimodalRetrieval, merge_filters


def test_merge_filters_with_should_and_modality():
    base = {"_should": [{"file_id": "f1"}, {"file_id": "f2"}]}
    merged = merge_filters(base, {"modality": "image"})
    assert merged == {
        "_should": [
            {"file_id": "f1", "modality": "image"},
            {"file_id": "f2", "modality": "image"},
        ]
    }


def test_multimodal_search_merges_text_and_image():
    text_hits = [{"id": "t1", "content": "text", "score": 0.8}]
    image_hits = [{"id": "i1", "content": "img", "score": 0.9, "metadata": {"modality": "image"}}]
    reranked = image_hits + text_hits

    with patch("retrieval.multimodal_retrieval.HybridSearch") as mock_cls, patch(
        "retrieval.multimodal_retrieval.RerankPipeline"
    ) as mock_rerank_cls:
        mock_search = MagicMock()
        mock_search.search.side_effect = [text_hits, image_hits]
        mock_cls.return_value = mock_search
        mock_rerank_cls.return_value.rerank.return_value = reranked

        hits = MultimodalRetrieval().search("query", top_k=5, filters={"file_id": "f1"})

    assert mock_search.search.call_count == 2
    image_call_filters = mock_search.search.call_args_list[1].kwargs["filters"]
    assert image_call_filters == {"file_id": "f1", "modality": "image"}
    assert len(hits) == 2
