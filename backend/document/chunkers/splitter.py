"""语义分块 + 固定长度分块，适配企业文档."""

import math
import re
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


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？.!?])\s*", text.strip())
    return [p.strip() for p in parts if p.strip()]


def split_semantic(text: str, **kwargs: Any) -> list[str]:
    """按语义边界分块：相邻句 embedding 相似度低于阈值处切分。"""
    cfg = get_settings()
    chunk_size = kwargs.get("chunk_size", cfg.chunk_size)
    threshold = kwargs.get("breakpoint_threshold", cfg.semantic_chunk_breakpoint_threshold)

    sentences = _split_sentences(text)
    if not sentences:
        return []
    if len(sentences) == 1:
        return split_by_fixed_length(sentences[0], chunk_size=chunk_size)

    from core.llm_factory import get_embedding

    embedding = get_embedding()
    vectors = embedding.embed_documents(sentences)

    breakpoints = [0]
    for i in range(len(sentences) - 1):
        sim = _cosine_similarity(vectors[i], vectors[i + 1])
        if sim < threshold:
            breakpoints.append(i + 1)
    breakpoints.append(len(sentences))

    segments: list[str] = []
    for start, end in zip(breakpoints, breakpoints[1:]):
        segment = "".join(sentences[start:end])
        if segment:
            segments.append(segment)

    chunks: list[str] = []
    for segment in segments:
        if len(segment) <= chunk_size:
            chunks.append(segment)
        else:
            chunks.extend(split_by_fixed_length(segment, chunk_size=chunk_size))
    return chunks


def split_document(
    chunks: list[dict[str, Any]],
    strategy: str = "fixed",
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """按指定策略切分文档块。"""
    result: list[dict[str, Any]] = []
    fixed_kwargs = {
        k: v for k, v in kwargs.items()
        if k in ("chunk_size", "overlap")
    }
    semantic_kwargs = {
        k: v for k, v in kwargs.items()
        if k in ("chunk_size", "breakpoint_threshold")
    }
    for chunk in chunks:
        content = chunk.get("content", "")
        if strategy == "semantic":
            parts = split_semantic(content, **semantic_kwargs)
        else:
            parts = split_by_fixed_length(content, **fixed_kwargs)
        for i, part in enumerate(parts):
            result.append({**chunk, "content": part, "chunk_index": i})
    return result
