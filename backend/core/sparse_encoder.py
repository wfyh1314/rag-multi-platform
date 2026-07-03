"""jieba 分词 + 词哈希稀疏向量编码（供 Qdrant BM25 风格检索）."""

import re
from collections import Counter

import jieba
from qdrant_client.models import SparseVector

from config.constants import SPARSE_VOCAB_SIZE

_TOKEN_PATTERN = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


class SparseEncoder:
    """将文本编码为 Qdrant SparseVector（term frequency，IDF 由 Qdrant 侧计算）。"""

    def __init__(self, vocab_size: int = SPARSE_VOCAB_SIZE):
        self.vocab_size = vocab_size

    def tokenize(self, text: str) -> list[str]:
        """中英文混合分词。"""
        text = text.strip().lower()
        if not text:
            return []
        tokens = list(jieba.cut(text, cut_all=False))
        cleaned: list[str] = []
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            for part in _TOKEN_PATTERN.findall(token):
                if len(part) > 1 or ("\u4e00" <= part <= "\u9fff"):
                    cleaned.append(part)
        return cleaned

    @staticmethod
    def _token_index(token: str, vocab_size: int) -> int:
        return hash(token) % vocab_size

    def encode(self, text: str) -> SparseVector:
        """单条文本 → SparseVector。"""
        tokens = self.tokenize(text)
        if not tokens:
            return SparseVector(indices=[], values=[])

        counts = Counter(self._token_index(t, self.vocab_size) for t in tokens)
        indices = sorted(counts.keys())
        values = [float(counts[i]) for i in indices]
        return SparseVector(indices=indices, values=values)

    def encode_batch(self, texts: list[str]) -> list[SparseVector]:
        """批量编码。"""
        return [self.encode(text) for text in texts]
