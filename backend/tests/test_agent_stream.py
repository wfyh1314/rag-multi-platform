"""Agent 流式端点测试."""

from unittest.mock import AsyncMock, patch


async def _fake_agent_stream(*args, **kwargs):
    from chat.sse_stream import format_sse_event

    yield format_sse_event({"content": "Agent"})
    yield format_sse_event({"sources": [{"content": "hit"}]})
    yield format_sse_event({"done": True})


def test_chat_agent_stream_returns_sse(client):
    with patch("api.chat_api.stream_agent_answer", side_effect=_fake_agent_stream), patch(
        "api.chat_api.content_risk"
    ) as mock_risk, patch("api.chat_api.history_service"), patch(
        "api.chat_api._persist_stream", side_effect=lambda fn, **kw: fn
    ):
        mock_risk.check.return_value = (True, [])
        resp = client.post(
            "/api/chat/agent/stream",
            json={"query": "hello agent", "session_id": "sess-1"},
        )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")
    assert "Agent" in resp.text
    assert "sources" in resp.text
