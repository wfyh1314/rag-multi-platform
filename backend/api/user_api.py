"""用户登录、注册、个人中心、角色权限接口."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.schemas import UserLoginRequest, UserRegisterRequest, UserUpdateRequest
from audit.op_log_service import OpLogService
from config.settings import Settings, get_settings
from core.response import success
from core.security import create_access_token, get_current_user
from user.user_service import UserService

router = APIRouter()
user_service = UserService()
op_log_service = OpLogService()


@router.post("/auth/register", summary="用户注册")
async def register(body: UserRegisterRequest) -> dict[str, Any]:
    """注册用户。"""
    user_data = user_service.register(
        body.username,
        body.password,
        department_id=body.department_id,
    )
    try:
        op_log_service.log(
            user_id=user_data["id"],
            action="user.register",
            resource_type="user",
            resource_id=user_data["id"],
            detail={"username": user_data["username"]},
        )
    except Exception:
        pass
    return success(result=user_data, message="注册成功")


@router.post("/auth/login", summary="用户登录")
async def login(body: UserLoginRequest) -> dict[str, Any]:
    """用户登录，返回 JWT 与人员信息。"""
    user_data = user_service.login(body.username, body.password)
    token = create_access_token(
        {
            "sub": user_data["id"],
            "role": user_data["role"],
            "department_id": user_data.get("department_id"),
        }
    )
    return success(
        result={
            "access_token": token,
            "token_type": "bearer",
            "user": user_data,
        },
        message="登录成功",
    )


@router.get("/users/me", summary="当前用户信息")
async def get_me(
    current_user: dict[str, Any] = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """获取当前用户信息。"""
    if settings.auth_skip:
        return success(
            result={
                "id": current_user.get("user_id", ""),
                "username": "dev-user",
                "role": current_user.get("role", "employee"),
                "real_name": "开发用户",
                "department_id": "default",
            },
            message="获取成功",
        )

    profile = user_service.get_profile(current_user.get("user_id", ""))
    if profile is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return success(result=profile, message="获取成功")


@router.put("/users/me", summary="更新个人信息")
async def update_me(
    body: UserUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """更新当前用户个人信息。"""
    user_id = current_user.get("user_id", "")
    profile = user_service.update_profile(
        user_id,
        real_name=body.real_name,
        phone=body.phone,
        email=body.email,
        department_id=body.department_id,
    )
    return success(result=profile, message="更新成功")
