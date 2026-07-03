"""文件工具、SimHash去重、时间工具、敏感词过滤、JWT工具."""

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


def get_file_extension(filename: str) -> str:
    """返回小写文件扩展名（含点号）。"""
    return Path(filename).suffix.lower()


def compute_file_hash(content: bytes) -> str:
    """计算文件内容的 SHA256 哈希。"""
    return hashlib.sha256(content).hexdigest()


def simhash(text: str, hash_bits: int = 64) -> int:
    """计算 SimHash 指纹，用于近似重复检测。"""
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return 0
    v = [0] * hash_bits
    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        for i in range(hash_bits):
            v[i] += 1 if (h >> i) & 1 else -1
    fingerprint = 0
    for i in range(hash_bits):
        if v[i] >= 0:
            fingerprint |= 1 << i
    return fingerprint


def hamming_distance(a: int, b: int) -> int:
    """计算两个 SimHash 值的汉明距离。"""
    return (a ^ b).bit_count()


def utc_now() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def format_datetime(dt: Optional[datetime] = None) -> str:
    """将 datetime 格式化为 ISO 字符串。"""
    return (dt or utc_now()).isoformat()


def filter_sensitive_words(text: str, word_list: Optional[Iterable[str]] = None) -> tuple[str, list[str]]:
    """过滤敏感词；返回清洗后文本与命中词列表。"""
    words = list(word_list or [])
    matched: list[str] = []
    result = text
    for word in words:
        if word and word in result:
            matched.append(word)
            result = result.replace(word, "*" * len(word))
    return result, matched


def decode_jwt_payload(token: str) -> dict:
    """解码 JWT 载荷（不校验签名，仅调试用）。"""
    import base64
    import json

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))
