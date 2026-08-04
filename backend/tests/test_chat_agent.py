"""Agent 问答 API 测试."""

from unittest.mock import MagicMock, patch


def test_chat_agent_returns_answer_and_sources(client):
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {
        "answer": "这是 Agent 回答",
        "sources": [{"doc_id": "1", "content": "片段", "metadata": {}, "score": 0.9}],
    }

    with patch("api.chat_api.build_rag_graph", return_value=mock_graph), patch(
        "api.chat_api.content_risk"
    ) as mock_risk, patch("api.chat_api.history_service"), patch(
        "api.chat_api._persist_assistant_message", return_value=None
    ):
        mock_risk.check.return_value = (True, [])
        resp = client.post(
            "/api/chat/agent",
            json={
                "query": "测试问题",
                "session_id": "sess-1",
                "collection": "file-abc",
                "tag_ids": ["tag-1"],
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["answer"] == "这是 Agent 回答"
    assert len(body["result"]["sources"]) == 1

    invoke_args = mock_graph.invoke.call_args[0][0]
    assert invoke_args["query"] == "测试问题"
    assert invoke_args["file_id"] == "file-abc"
    assert invoke_args["tag_ids"] == ["tag-1"]
    assert "user" in invoke_args


def test_chat_agent_content_risk_blocked(client):
    with patch("api.chat_api.content_risk") as mock_risk:
        mock_risk.check.return_value = (False, ["敏感词"])
        resp = client.post("/api/chat/agent", json={"query": "敏感词"})

    assert resp.status_code == 200
    assert "敏感词" in resp.json()["result"]["answer"]
    assert resp.json()["result"]["sources"] == []
