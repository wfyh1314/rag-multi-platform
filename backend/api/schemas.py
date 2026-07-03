"""Pydantic 请求/响应模型、租户/用户/文件/对话校验."""

from datetime import datetime
from typing import Any, Optional

from pydantic import AliasChoices, BaseModel, Field


# ---------- 通用 ----------

class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]


# ---------- 租户 ----------

class TenantCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    max_users: Optional[int] = None
    max_storage_mb: Optional[int] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    status: str = "active"
    created_at: Optional[datetime] = None


# ---------- 用户 ----------

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    tenant_id: str


class UserLoginRequest(BaseModel):
    username: str
    password: str
    tenant_id: str


class UserResponse(BaseModel):
    id: str
    username: str
    tenant_id: str
    role: str = "employee"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------- 文件 ----------

class FileUploadResponse(BaseModel):
    file_id: Optional[str] = None
    filename: str
    status: str
    message: str
    tenant_id: Optional[str] = None
    chunk_count: Optional[int] = None


class FileItemResponse(BaseModel):
    file_id: str
    filename: str
    status: str
    chunk_count: Optional[int] = None
    message: Optional[str] = None
    uploaded_at: Optional[str] = None


class FileListResponse(BaseModel):
    files: list[FileItemResponse]
    total: int


class FolderCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    parent_id: Optional[str] = None


class FileMoveRequest(BaseModel):
    file_id: str
    folder_id: str


# ---------- 对话 ----------

class ChatStreamRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices("query", "question"),
    )
    session_id: Optional[str] = None
    collection: Optional[str] = None
    model: Optional[str] = None
    history: Optional[list[dict[str, str]]] = None
    temperature: Optional[float] = None
    max_length: Optional[int] = None


class HistoryClearRequest(BaseModel):
    session_id: str


class SessionCreateRequest(BaseModel):
    title: Optional[str] = "新对话"


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: Optional[datetime] = None


# ---------- 审计 ----------

class AuditQueryRequest(BaseModel):
    action: Optional[str] = None
    user_id: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
