"""SparseEncoder 单元测试."""

from core.sparse_encoder import SparseEncoder


def test_encode_empty_text():
    encoder = SparseEncoder()
    result = encoder.encode("")
    assert result.indices == []
    assert result.values == []


def test_encode_same_text_same_vector():
    encoder = SparseEncoder()
    text = "企业知识库混合检索测试"
    a = encoder.encode(text)
    b = encoder.encode(text)
    assert a.indices == b.indices
    assert a.values == b.values


def test_encode_batch_length():
    encoder = SparseEncoder()
    texts = ["第一段文本", "第二段文本"]
    results = encoder.encode_batch(texts)
    assert len(results) == 2
    assert len(results[0].indices) > 0
