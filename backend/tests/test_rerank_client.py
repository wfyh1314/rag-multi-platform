"""DashScope Rerank 客户端测试."""

from unittest.mock import MagicMock, patch

from config.settings import get_settings
from core.llm_factory import DashScopeRerankClient


def test_rerank_client_request_payload(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    get_settings.cache_clear()
    settings = get_settings()
    client = DashScopeRerankClient(settings)

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "output": {
            "results": [
                {"index": 1, "relevance_score": 0.88},
                {"index": 0, "relevance_score": 0.55},
            ]
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_client_cls:
        mock_http = MagicMock()
        mock_http.__enter__.return_value = mock_http
        mock_http.__exit__.return_value = False
        mock_http.post.return_value = mock_response
        mock_client_cls.return_value = mock_http

        results = client.rerank(
            "query text",
            ["doc a", "doc b"],
            top_n=2,
        )

    mock_http.post.assert_called_once()
    call_kwargs = mock_http.post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "gte-rerank-v2"
    assert call_kwargs["json"]["input"]["query"] == "query text"
    assert call_kwargs["json"]["input"]["documents"] == ["doc a", "doc b"]
    assert call_kwargs["json"]["parameters"]["top_n"] == 2
    assert call_kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert results == [
        {"index": 1, "relevance_score": 0.88},
        {"index": 0, "relevance_score": 0.55},
    ]
    get_settings.cache_clear()
