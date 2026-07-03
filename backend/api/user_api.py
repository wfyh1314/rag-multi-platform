"""用户登录、注册、个人中心、角色权限接口."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.schemas import (
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from core.security import get_current_user
from tenant.user_service import UserService

router = APIRouter()
user_service = UserService()


@router.post("/auth/register", response_model=UserResponse, summary="用户注册")
async def register(body: UserRegisterRequest) -> UserResponse:
    """注册用户（占位）。"""
    raise HTTPException(status_code=501, detail="用户注册接口待实现")


@router.post("/auth/login", response_model=TokenResponse, summary="用户登录")
async def login(body: UserLoginRequest) -> TokenResponse:
    """用户登录（占位）。"""
    raise HTTPException(status_code=501, detail="用户登录接口待实现")


@router.get("/users/me", response_model=UserResponse, summary="当前用户信息")
async def get_me(current_user: dict[str, Any] = Depends(get_current_user)) -> UserResponse:
    """获取当前用户信息。"""
    return UserResponse(
        id=current_user.get("user_id", ""),
        username="dev-user",
        tenant_id=current_user.get("tenant_id", ""),
        role=current_user.get("role", "employee"),
    )


@router.put("/users/me", response_model=MessageResponse, summary="更新个人信息")
async def update_me(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> MessageResponse:
    """更新当前用户个人信息（占位）。"""
    raise HTTPException(status_code=501, detail="个人信息更新接口待实现")
