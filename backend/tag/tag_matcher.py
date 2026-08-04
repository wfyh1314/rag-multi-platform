"""标签关键词匹配."""

import re
from typing import Iterable

from storage.models.tag import Tag

_KEYWORD_SPLIT_RE = re.compile(r"[,，、;\s]+")


def parse_keywords(keywords: str) -> list[str]:
    """将关键词字符串拆分为列表。"""
    if not keywords:
        return []
    return [item.strip() for item in _KEYWORD_SPLIT_RE.split(keywords) if item.strip()]


def match_tag_ids(content: str, tags: Iterable[Tag]) -> list[str]:
    """根据正文内容匹配命中的标签 ID。"""
    if not content:
        return []

    content_lower = content.lower()
    matched: list[str] = []
    seen: set[str] = set()

    for tag in tags:
        for keyword in parse_keywords(tag.keywords):
            if keyword.lower() in content_lower and tag.id not in seen:
                matched.append(tag.id)
                seen.add(tag.id)
                break

    return matched
