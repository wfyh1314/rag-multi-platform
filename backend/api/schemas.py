"""Pydantic 请求/响应模型、用户/文件/对话校验."""

from datetime import datetime
from typing import Any, Optional

from pydantic import AliasChoices, BaseModel, Field


# ---------- 通用 ----------

class ApiResponse(BaseModel):
    code: int
    description: str = ""
    message: str = ""
    result: Any | None = None
    uuid: str = ""


class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]


# ---------- 用户 ----------

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    department_id: Optional[str] = Field(None, max_length=64, description="所属部门 ID")


class UserUpdateRequest(BaseModel):
    real_name: Optional[str] = Field(None, max_length=64)
    phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=128)
    department_id: Optional[str] = Field(None, max_length=64)


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    role: str = "employee"
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[str] = None


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
    visibility: Optional[str] = None
    chunk_count: Optional[int] = None


class FileItemResponse(BaseModel):
    file_id: str
    filename: str
    status: str
    visibility: Optional[str] = None
    chunk_count: Optional[int] = None
    message: Optional[str] = None
    uploaded_at: Optional[str] = None


class FileListResponse(BaseModel):
    files: list[FileItemResponse]
    total: int


class FolderCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    parent_id: Optional[str] = None


class FolderRenameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)


class FolderMoveRequest(BaseModel):
    parent_id: Optional[str] = None


class FileMoveRequest(BaseModel):
    file_id: str
    folder_id: str = ""


class FileStatusUpdateRequest(BaseModel):
    status: str = Field(..., min_length=1, max_length=32)


# ---------- 标签 ----------

class TagCategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)


class TagCategoryUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)


class TagCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    keywords: str = Field(default="")


class TagUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    keywords: str = Field(default="")


class TagResponse(BaseModel):
    id: str
    category_id: str
    name: str
    keywords: str
    category_name: Optional[str] = None
    created_at: Optional[str] = None


class TagCategoryResponse(BaseModel):
    id: str
    name: str
    sort_order: int
    tag_count: int
    tags: list[TagResponse] = []
    created_at: Optional[str] = None


class FileTagItemResponse(BaseModel):
    tag_id: str
    tag_name: str
    category_id: str
    category_name: str
    keywords: Optional[str] = None
    source: str
    label: str


class FileWithTagsResponse(BaseModel):
    file_id: str
    filename: str
    status: str
    visibility: Optional[str] = None
    chunk_count: Optional[int] = None
    message: Optional[str] = None
    uploaded_at: Optional[str] = None
    tags: list[FileTagItemResponse] = []


class FileTagsUpdateRequest(BaseModel):
    tag_ids: list[str] = Field(default_factory=list)


class FileTagsRerunRequest(BaseModel):
    file_ids: Optional[list[str]] = None


# ---------- 对话 ----------

class ChatStreamRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices("query", "question"),
    )
    session_id: Optional[str] = None
    collection: Optional[str] = Field(None, description="知识库 file_id")
    tag_ids: Optional[list[str]] = Field(default=None, description="标签 ID 列表，RAG 检索过滤")
    model: Optional[str] = None
    history: Optional[list[dict[str, str]]] = None
    temperature: Optional[float] = None
    max_length: Optional[int] = None


class AgentChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    collection: Optional[str] = Field(None, description="知识库 file_id")
    tag_ids: Optional[list[str]] = Field(default=None, description="标签 ID 列表")


class AgentChatResponse(BaseModel):
    answer: str
    sources: list[Any] = Field(default_factory=list)


class HistoryClearRequest(BaseModel):
    session_id: str


class SessionCreateRequest(BaseModel):
    title: Optional[str] = "新对话"


class SessionImportRequest(BaseModel):
    sessions: list[dict[str, Any]] = Field(default_factory=list)


class SessionUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: list[Any] = Field(default_factory=list)
    created_at: Optional[str] = None


# ---------- 审计 ----------

class AuditQueryRequest(BaseModel):
    action: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
