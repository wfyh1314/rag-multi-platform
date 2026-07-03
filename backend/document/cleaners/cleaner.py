"""文档清洗：去水印、空行、重复段落、脏数据过滤."""

import re
from typing import Any


def remove_empty_lines(text: str) -> str:
    """去除连续空行。"""
    return re.sub(r"\n{3,}", "\n\n", text.strip())


def remove_watermarks(text: str, patterns: list[str] | None = None) -> str:
    """去除文本中的水印模式。"""
    result = text
    for pattern in patterns or []:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    return result


def deduplicate_paragraphs(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按内容哈希去除重复段落。"""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for chunk in chunks:
        content = chunk.get("content", "")
        if content and content not in seen:
            seen.add(content)
            unique.append(chunk)
    return unique


def clean_document(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """对文档块执行完整清洗流程。"""
    cleaned = []
    for chunk in chunks:
        content = chunk.get("content", "")
        content = remove_empty_lines(content)
        cleaned.append({**chunk, "content": content})
    return deduplicate_paragraphs(cleaned)
