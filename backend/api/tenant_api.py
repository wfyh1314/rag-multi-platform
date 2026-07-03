"""租户管理、企业管理员后台接口."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.schemas import MessageResponse, TenantCreateRequest, TenantResponse
from core.security import get_current_user
from tenant.tenant_service import TenantService

router = APIRouter()
tenant_service = TenantService()


@router.post("/tenants", response_model=TenantResponse, summary="创建租户")
async def create_tenant(
    body: TenantCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> TenantResponse:
    """创建租户（占位）。"""
    raise HTTPException(status_code=501, detail="租户创建接口待实现")


@router.get("/tenants/{tenant_id}", response_model=TenantResponse, summary="获取租户详情")
async def get_tenant(
    tenant_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> TenantResponse:
    """按 ID 获取租户（占位）。"""
    raise HTTPException(status_code=501, detail="租户详情接口待实现")


@router.put("/tenants/{tenant_id}", response_model=TenantResponse, summary="更新租户")
async def update_tenant(
    tenant_id: str,
    body: TenantCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> TenantResponse:
    """更新租户（占位）。"""
    raise HTTPException(status_code=501, detail="租户更新接口待实现")


@router.delete("/tenants/{tenant_id}", response_model=MessageResponse, summary="删除租户")
async def delete_tenant(
    tenant_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> MessageResponse:
    """删除租户（占位）。"""
    raise HTTPException(status_code=501, detail="租户删除接口待实现")
