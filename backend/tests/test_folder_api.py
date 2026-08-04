"""文件夹 API 测试."""

from unittest.mock import patch


def test_folder_crud_flow(client):
    create_resp = client.post("/api/folders", json={"name": "项目文档"})
    assert create_resp.status_code == 200
    folder_id = create_resp.json()["result"]["id"]

    tree_resp = client.get("/api/folders")
    assert tree_resp.status_code == 200
    folders = tree_resp.json()["result"]["folders"]
    assert any(f["id"] == folder_id for f in folders)

    rename_resp = client.put(f"/api/folders/{folder_id}", json={"name": "归档文档"})
    assert rename_resp.status_code == 200
    assert rename_resp.json()["result"]["name"] == "归档文档"

    child_resp = client.post(
        "/api/folders",
        json={"name": "子目录", "parent_id": folder_id},
    )
    assert child_resp.status_code == 200
    child_id = child_resp.json()["result"]["id"]

    delete_child = client.delete(f"/api/folders/{child_id}")
    assert delete_child.status_code == 200

    delete_resp = client.delete(f"/api/folders/{folder_id}")
    assert delete_resp.status_code == 200


def test_upload_with_folder_id(client):
    folder_resp = client.post("/api/folders", json={"name": "上传目录"})
    folder_id = folder_resp.json()["result"]["id"]

    with patch("api.file_api.file_service.upload") as mock_upload:
        mock_upload.return_value = {
            "file_id": "f-test-001",
            "filename": "demo.txt",
            "visibility": "private",
            "status": "indexed",
            "message": "ok",
            "chunk_count": 1,
            "folder_id": folder_id,
        }
        resp = client.post(
            "/api/upload",
            data={"visibility": "private", "folder_id": folder_id},
            files={"file": ("demo.txt", b"hello", "text/plain")},
        )
    assert resp.status_code == 200
    mock_upload.assert_called_once()
    assert mock_upload.call_args.kwargs.get("folder_id") == folder_id
