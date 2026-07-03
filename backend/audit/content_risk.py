"""输入敏感词过滤、违规内容拦截."""

from typing import Iterable, Optional, Tuple

from core.utils import filter_sensitive_words


# 默认敏感词列表（占位）
DEFAULT_SENSITIVE_WORDS: list[str] = []


class ContentRiskService:
    """内容风险检测与过滤。"""

    def __init__(self, word_list: Optional[Iterable[str]] = None):
        self.word_list = list(word_list or DEFAULT_SENSITIVE_WORDS)

    def check(self, text: str) -> Tuple[bool, list[str]]:
        """检测文本是否含敏感内容，返回 (是否安全, 命中词列表)。"""
        _, matched = filter_sensitive_words(text, self.word_list)
        return len(matched) == 0, matched

    def filter(self, text: str) -> str:
        """过滤文本中的敏感词。"""
        filtered, _ = filter_sensitive_words(text, self.word_list)
        return filtered

    def require_safe(self, text: str) -> None:
        """文本含敏感内容时抛出异常。"""
        is_safe, matched = self.check(text)
        if not is_safe:
            from core.exceptions import ValidationError
            raise ValidationError(f"内容包含敏感词: {', '.join(matched)}")
