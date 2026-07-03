"""语义分块 + 固定长度分块，适配企业文档."""

from typing import Any

from config.settings import get_settings


def split_by_fixed_length(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    """按固定长度与重叠分块。"""
    cfg = get_settings()
    size = chunk_size if chunk_size is not None else cfg.chunk_size
    ovlp = overlap if overlap is not None else cfg.chunk_overlap
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - ovlp
        if start >= len(text):
            break
    return chunks


def split_semantic(text: str, **kwargs: Any) -> list[str]:
    """按语义边界分块（占位）。"""
    raise NotImplementedError("Semantic splitting not yet implemented")


def split_document(
    chunks: list[dict[str, Any]],
    strategy: str = "fixed",
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """按指定策略切分文档块。"""
    result: list[dict[str, Any]] = []
    for chunk in chunks:
        content = chunk.get("content", "")
        if strategy == "fixed":
            parts = split_by_fixed_length(content, **kwargs)
        else:
            parts = split_semantic(content, **kwargs)
        for i, part in enumerate(parts):
            result.append({**chunk, "content": part, "chunk_index": i})
    return result
