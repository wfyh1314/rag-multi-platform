"""会话归档 API 测试."""


def test_archive_session(client):
    create_resp = client.post("/api/sessions", json={"title": "待归档"})
    assert create_resp.status_code == 200
    session_id = create_resp.json()["result"]["id"]

    archive_resp = client.post(f"/api/sessions/{session_id}/archive")
    assert archive_resp.status_code == 200
    assert archive_resp.json()["result"]["is_archived"] is True

    list_resp = client.get("/api/sessions")
    ids = [item["id"] for item in list_resp.json()["result"]["sessions"]]
    assert session_id not in ids

    archived_resp = client.get("/api/sessions", params={"include_archived": True})
    archived_ids = [item["id"] for item in archived_resp.json()["result"]["sessions"]]
    assert session_id in archived_ids
