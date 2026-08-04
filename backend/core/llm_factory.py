"""LLM/Embedding/Rerank 统一工厂（阿里通义 DashScope OpenAI 兼容模式）."""

import json
from collections.abc import Iterator
from typing import Any, Optional, Protocol

import httpx

from config.settings import Settings, get_settings
from config.response_codes import INTERNAL_ERROR
from core.exceptions import AppError


class LLMClient(Protocol):
    """LLM 客户端协议。"""

    def invoke(self, messages: list[dict[str, str]], **kwargs: Any) -> str: ...

    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]: ...


class EmbeddingClient(Protocol):
    """Embedding 客户端协议。"""

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class RerankClient(Protocol):
    """Rerank 客户端协议。"""

    def rerank(self, query: str, documents: list[str], top_n: int = 5) -> list[dict[str, Any]]: ...


class DashScopeEmbeddingClient:
    """DashScope OpenAI 兼容 Embedding 客户端."""

    def __init__(self, settings: Settings):
        self.api_base = settings.embedding_api_base.rstrip("/")
        self.api_key = settings.embedding_api_key
        self.model = settings.embedding_model

        if not self.api_key:
            raise AppError(
                "未配置 DASHSCOPE_API_KEY，无法向量化",
                code=INTERNAL_ERROR,
                status_code=503,
            )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, texts: list[str]) -> list[list[float]]:
        url = f"{self.api_base}/embeddings"
        payload = {"model": self.model, "input": texts}

        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=self._headers())
            response.raise_for_status()
            data = response.json()

        items = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in items]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        batch_size = 64
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            all_embeddings.extend(self._request(batch))
        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        return self._request([text])[0]


class DashScopeRerankClient:
    """DashScope 文本 Rerank 客户端（gte-rerank-v2）."""

    def __init__(self, settings: Settings):
        self.api_url = settings.rerank_api_url
        self.api_key = settings.effective_rerank_api_key
        self.model = settings.rerank_model

        if not self.api_key:
            raise AppError(
                "未配置 DASHSCOPE_API_KEY，无法调用 Rerank",
                code=INTERNAL_ERROR,
                status_code=503,
            )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def rerank(self, query: str, documents: list[str], top_n: int = 5) -> list[dict[str, Any]]:
        if not documents:
            return []

        payload = {
            "model": self.model,
            "input": {
                "query": query,
                "documents": documents,
            },
            "parameters": {
                "top_n": min(top_n, len(documents)),
                "return_documents": False,
            },
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(self.api_url, json=payload, headers=self._headers())
            response.raise_for_status()
            data = response.json()

        results = data.get("output", {}).get("results", [])
        return [
            {
                "index": item["index"],
                "relevance_score": item.get("relevance_score", 0.0),
            }
            for item in results
        ]


class DashScopeLLMClient:
    """DashScope OpenAI 兼容 Chat Completions 客户端."""

    def __init__(self, settings: Settings):
        self.api_base = settings.llm_api_base.rstrip("/")
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

        if not self.api_key:
            raise AppError(
                "未配置 DASHSCOPE_API_KEY，无法调用 LLM",
                code=INTERNAL_ERROR,
                status_code=503,
            )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, messages: list[dict[str, str]], stream: bool, **kwargs: Any) -> dict[str, Any]:
        return {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": stream,
        }

    def invoke(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        url = f"{self.api_base}/chat/completions"
        payload = self._build_payload(messages, stream=False, **kwargs)

        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=payload, headers=self._headers())
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"]

    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]:
        url = f"{self.api_base}/chat/completions"
        payload = self._build_payload(messages, stream=True, **kwargs)

        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", url, json=payload, headers=self._headers()) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


_llm_instance: Optional[Any] = None
_embedding_instance: Optional[Any] = None
_rerank_instance: Optional[Any] = None


def get_llm(settings: Optional[Settings] = None) -> DashScopeLLMClient:
    """返回 DashScope LLM 单例客户端。"""
    global _llm_instance
    if _llm_instance is None:
        cfg = settings or get_settings()
        _llm_instance = DashScopeLLMClient(cfg)
    return _llm_instance


def get_embedding(settings: Optional[Settings] = None) -> DashScopeEmbeddingClient:
    """返回 DashScope Embedding 单例客户端。"""
    global _embedding_instance
    if _embedding_instance is None:
        cfg = settings or get_settings()
        _embedding_instance = DashScopeEmbeddingClient(cfg)
    return _embedding_instance


def get_reranker(settings: Optional[Settings] = None) -> DashScopeRerankClient:
    """返回 DashScope Rerank 单例客户端。"""
    global _rerank_instance
    if _rerank_instance is None:
        cfg = settings or get_settings()
        _rerank_instance = DashScopeRerankClient(cfg)
    return _rerank_instance
