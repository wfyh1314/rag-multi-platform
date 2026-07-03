"""文件上传、文件夹管理、文件预览接口."""

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from api.schemas import (
    FileListResponse,
    FileUploadResponse,
    FolderCreateRequest,
    MessageResponse,
)
from config.settings import get_settings
from core.security import get_current_user
from file_mgr.file_service import FileService, list_collections_for_tenant, list_files_for_tenant
from file_mgr.folder_service import FolderService

router = APIRouter()
file_service = FileService()
folder_service = FolderService()


# ---------- 前端兼容路由 ----------

@router.get("/models", summary="可用 LLM 模型列表（前端兼容）")
async def list_models(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, list[dict[str, str]]]:
    """返回前端可用的 LLM 模型列表。"""
    settings = get_settings()
    model = settings.llm_model
    return {"models": [{"id": model, "name": model}]}


@router.get("/collections", summary="知识库集合列表（前端兼容）")
async def list_collections(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, list]:
    """返回当前租户已上传的知识库文件列表。"""
    tenant_id = current_user.get("tenant_id", "")
    return list_collections_for_tenant(tenant_id)


@router.get("/files", response_model=FileListResponse, summary="文件列表（支持模糊搜索）")
async def list_files(
    keyword: str | None = Query(None, description="文件名模糊搜索"),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> FileListResponse:
    """返回当前租户已上传文件列表。"""
    tenant_id = current_user.get("tenant_id", "")
    result = list_files_for_tenant(tenant_id, keyword)
    return FileListResponse(**result)


@router.post("/upload", response_model=FileUploadResponse, summary="文件上传（前端兼容）")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> FileUploadResponse:
    """上传文件并触发异步解析。"""
    content = await file.read()
    from io import BytesIO

    result = file_service.upload(
        file=BytesIO(content),
        filename=file.filename or "unknown",
        tenant_id=current_user.get("tenant_id", ""),
        user_id=current_user.get("user_id", ""),
    )
    return FileUploadResponse(
        file_id=result["file_id"],
        filename=result["filename"],
        status=result["status"],
        message=result["message"],
        tenant_id=result["tenant_id"],
        chunk_count=result["chunk_count"],
    )


# ---------- 文件夹管理 ----------

@router.post("/folders", summary="创建文件夹")
async def create_folder(
    body: FolderCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """创建文件夹（占位）。"""
    raise HTTPException(status_code=501, detail="文件夹创建接口待实现")


@router.get("/folders", summary="文件夹树")
async def list_folders(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, list]:
    """获取文件夹树（占位）。"""
    return {"folders": []}


@router.get("/files/{file_id}/preview", summary="文件预览")
async def preview_file(
    file_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """预览文件内容（占位）。"""
    raise HTTPException(status_code=501, detail="文件预览接口待实现")


@router.delete("/files/{file_id}", response_model=MessageResponse, summary="删除文件")
async def delete_file(
    file_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> MessageResponse:
    """删除文件及其向量索引。"""
    tenant_id = current_user.get("tenant_id", "")
    file_service.delete(file_id, tenant_id)
    return MessageResponse(message="文件已删除")
