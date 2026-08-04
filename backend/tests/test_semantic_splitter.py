"""语义分块测试."""

from unittest.mock import MagicMock, patch

from document.chunkers.splitter import split_semantic


def test_split_semantic_single_sentence_fallback():
    with patch("document.chunkers.splitter.split_by_fixed_length", return_value=["part"]) as mock_fixed:
        result = split_semantic("只有一句。")
    mock_fixed.assert_called_once()
    assert result == ["part"]


def test_split_semantic_with_embeddings():
    sentences = ["第一句。", "第二句。", "第三句。"]
    text = "".join(sentences)
    mock_embedding = MagicMock()
    mock_embedding.embed_documents.return_value = [
        [1.0, 0.0],
        [0.9, 0.1],
        [0.0, 1.0],
    ]
    with patch("core.llm_factory.get_embedding", return_value=mock_embedding):
        chunks = split_semantic(text, chunk_size=500, breakpoint_threshold=0.5)
    assert len(chunks) >= 1
    assert all(isinstance(c, str) for c in chunks)
