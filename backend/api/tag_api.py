"""标签字典与文档打标接口."""

from typing import Any

from fastapi import APIRouter, Depends, Query

from api.schemas import (
    FileTagsRerunRequest,
    FileTagsUpdateRequest,
    TagCategoryCreateRequest,
    TagCategoryUpdateRequest,
    TagCreateRequest,
    TagUpdateRequest,
)
from core.response import success
from core.security import get_current_user
from tag.tag_service import TagService

router = APIRouter()
tag_service = TagService()


@router.get("/tag-categories", summary="标签分类树")
async def list_tag_categories(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    return success(result=tag_service.list_categories_tree(), message="获取成功")


@router.post("/tag-categories", summary="新增标签分类")
async def create_tag_category(
    body: TagCategoryCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    result = tag_service.create_category(body.name)
    return success(result=result, message="创建成功")


@router.put("/tag-categories/{category_id}", summary="更新标签分类")
async def update_tag_category(
    category_id: str,
    body: TagCategoryUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    result = tag_service.update_category(category_id, body.name)
    return success(result=result, message="更新成功")


@router.delete("/tag-categories/{category_id}", summary="删除标签分类")
async def delete_tag_category(
    category_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    tag_service.delete_category(category_id)
    return success(message="删除成功")


@router.post("/tag-categories/{category_id}/tags", summary="新增标签")
async def create_tag(
    category_id: str,
    body: TagCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    result = tag_service.create_tag(category_id, body.name, body.keywords)
    return success(result=result, message="创建成功")


@router.put("/tags/{tag_id}", summary="更新标签")
async def update_tag(
    tag_id: str,
    body: TagUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    result = tag_service.update_tag(tag_id, body.name, body.keywords)
    return success(result=result, message="更新成功")


@router.delete("/tags/{tag_id}", summary="删除标签")
async def delete_tag(
    tag_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    tag_service.delete_tag(tag_id)
    return success(message="删除成功")


@router.get("/files/with-tags", summary="文档列表（含标签）")
async def list_files_with_tags(
    keyword: str | None = Query(None, description="文件名模糊搜索"),
    folder_id: str | None = Query(None, description="文件夹 ID，传空字符串表示根目录"),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    user_id = current_user.get("user_id", "")
    result = tag_service.list_files_with_tags(user_id, keyword, folder_id=folder_id)
    return success(result=result, message="获取成功")


@router.get("/files/{file_id}/tags", summary="单文档标签详情")
async def get_file_tags(
    file_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    result = tag_service.get_file_tags(current_user, file_id)
    return success(result=result, message="获取成功")


@router.put("/files/{file_id}/tags", summary="手动设置文档标签")
async def set_file_tags(
    file_id: str,
    body: FileTagsUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    result = tag_service.set_manual_file_tags(current_user, file_id, body.tag_ids)
    return success(result=result, message="保存成功")


@router.post("/files/tags/rerun", summary="批量重跑自动打标")
async def rerun_file_tags(
    body: FileTagsRerunRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    result = tag_service.rerun_auto_tags(current_user, body.file_ids)
    return success(result=result, message="重跑完成")
