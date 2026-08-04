"""文件上传、文件夹管理、文件预览接口."""

from typing import Any

from fastapi import APIRouter, Depends, File, Form, Path, Query, UploadFile

from api.schemas import (
    FileMoveRequest,
    FileStatusUpdateRequest,
    FolderCreateRequest,
    FolderMoveRequest,
    FolderRenameRequest,
)
from config.constants import DOC_VISIBILITY_PRIVATE
from config.settings import get_settings
from core.response import success
from core.security import get_current_user
from file_mgr.file_service import FileService, list_collections_for_user, list_files_for_user
from file_mgr.folder_service import FolderService

router = APIRouter()
file_service = FileService()
folder_service = FolderService()

FILE_ID_PATH = Path(..., pattern=r"^[0-9a-fA-F-]{36}$")


# ---------- 前端兼容路由 ----------

@router.get("/models", summary="可用 LLM 模型列表（前端兼容）")
async def list_models(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """返回前端可用的 LLM 模型列表。"""
    settings = get_settings()
    model = settings.llm_model
    return success(
        result={"models": [{"id": model, "name": model}]},
        message="获取成功",
    )


@router.get("/collections", summary="知识库集合列表（前端兼容）")
async def list_collections(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """返回当前用户可访问的知识库文件列表。"""
    user_id = current_user.get("user_id", "")
    return success(result=list_collections_for_user(user_id), message="获取成功")


@router.get("/files", summary="文件列表（支持模糊搜索）")
async def list_files(
    keyword: str | None = Query(None, description="文件名模糊搜索"),
    folder_id: str | None = Query(None, description="文件夹 ID，传空字符串表示根目录"),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """返回当前用户可访问的文件列表。"""
    user_id = current_user.get("user_id", "")
    result = list_files_for_user(user_id, keyword, folder_id=folder_id)
    return success(result=result, message="获取成功")


@router.post("/upload", summary="文件上传（前端兼容）")
async def upload_file(
    file: UploadFile = File(...),
    visibility: str = Form(default=DOC_VISIBILITY_PRIVATE),
    folder_id: str | None = Form(default=None),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """上传文件并触发解析入库。"""
    content = await file.read()
    from io import BytesIO

    result = file_service.upload(
        file=BytesIO(content),
        filename=file.filename or "unknown",
        user_id=current_user.get("user_id", ""),
        visibility=visibility,
        folder_id=folder_id or None,
        department_id=current_user.get("department_id"),
    )
    return success(
        result={
            "file_id": result["file_id"],
            "filename": result["filename"],
            "visibility": result["visibility"],
            "status": result["status"],
            "message": result["message"],
            "chunk_count": result["chunk_count"],
        },
        message="上传成功",
    )


# ---------- 文件夹管理 ----------

@router.post("/folders", summary="创建文件夹")
async def create_folder(
    body: FolderCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """创建文件夹。"""
    result = folder_service.create(
        body.name,
        parent_id=body.parent_id,
        user_id=current_user.get("user_id", ""),
    )
    return success(result=result, message="创建成功")


@router.get("/folders", summary="文件夹树")
async def list_folders(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """获取文件夹树。"""
    folders = folder_service.list_tree(user_id=current_user.get("user_id", ""))
    return success(result={"folders": folders}, message="获取成功")


FOLDER_ID_PATH = Path(..., pattern=r"^[0-9a-fA-F-]{36}$")


@router.put("/folders/{folder_id}", summary="重命名文件夹")
async def rename_folder(
    folder_id: str = FOLDER_ID_PATH,
    body: FolderRenameRequest = ...,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """重命名文件夹。"""
    result = folder_service.rename(folder_id, body.name, current_user.get("user_id", ""))
    return success(result=result, message="更新成功")


@router.put("/folders/{folder_id}/move", summary="移动文件夹")
async def move_folder(
    folder_id: str = FOLDER_ID_PATH,
    body: FolderMoveRequest = ...,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """将文件夹移动到新的父级。"""
    result = folder_service.move(folder_id, body.parent_id, current_user.get("user_id", ""))
    return success(result=result, message="移动成功")


@router.delete("/folders/{folder_id}", summary="删除文件夹")
async def delete_folder(
    folder_id: str = FOLDER_ID_PATH,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """删除空文件夹。"""
    folder_service.delete(folder_id, current_user.get("user_id", ""))
    return success(message="删除成功")


@router.get("/files/{file_id}/preview", summary="文件预览")
async def preview_file(
    file_id: str = FILE_ID_PATH,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """预览文件内容。"""
    result = file_service.preview(file_id, current_user)
    return success(result=result, message="获取成功")


@router.put("/files/{file_id}/move", summary="移动文件")
async def move_file(
    file_id: str = FILE_ID_PATH,
    body: FileMoveRequest = ...,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """将文件移动到指定文件夹。"""
    result = file_service.move(file_id, body.folder_id, current_user)
    return success(result=result, message="移动成功")


@router.patch("/files/{file_id}/status", summary="更新文件状态")
async def update_file_status(
    file_id: str = FILE_ID_PATH,
    body: FileStatusUpdateRequest = ...,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """更新文件解析/索引状态。"""
    result = file_service.update_status(file_id, body.status, current_user)
    return success(result=result, message="更新成功")


@router.delete("/files/{file_id}", summary="删除文件")
async def delete_file(
    file_id: str = FILE_ID_PATH,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """删除文件及其向量索引。"""
    file_service.delete(file_id, current_user)
    return success(message="文件已删除")
