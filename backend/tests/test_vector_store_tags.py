"""VectorStore tag_ids 过滤测试."""

from storage.vector_store import VectorStore


def test_build_tag_filter_single():
    condition = VectorStore._build_tag_filter("tag-a")
    assert condition.key == "tag_ids"


def test_build_tag_filter_multiple():
    filt = VectorStore._build_tag_filter(["tag-a", "tag-b"])
    assert filt.should is not None
    assert len(filt.should) == 2


def test_build_filter_combines_file_and_tags():
    filt = VectorStore()._build_filter({"file_id": "f1", "tag_ids": ["t1"]})
    assert filt.must is not None
    assert len(filt.must) == 2
