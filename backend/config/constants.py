"""业务常量：单文件最大限制、分块尺寸、JWT过期时间、租户限额."""

# 文件上传限制
MAX_UPLOAD_SIZE_MB: int = 50
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({
    ".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".CSV",
    ".png", ".jpg", ".jpeg", ".webp",
})

# 分块（尺寸见 Settings / .env 中 CHUNK_SIZE、CHUNK_OVERLAP）
SEMANTIC_CHUNK_THRESHOLD: float = 0.75

# JWT 令牌
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

# 租户配额（新租户默认值）
DEFAULT_MAX_USERS: int = 100
DEFAULT_MAX_FILES: int = 10000
DEFAULT_MAX_STORAGE_MB: int = 10240
DEFAULT_MAX_CHAT_SESSIONS: int = 500

# 检索
DEFAULT_TOP_K: int = 10
DEFAULT_RERANK_TOP_N: int = 5
HYBRID_DENSE_WEIGHT: float = 0.6
HYBRID_SPARSE_WEIGHT: float = 0.4
HYBRID_PREFETCH_LIMIT: int = 20
DENSE_VECTOR_NAME: str = "dense"
SPARSE_VECTOR_NAME: str = "sparse"
SPARSE_VOCAB_SIZE: int = 1 << 20

# RBAC 角色
ROLE_SUPER_ADMIN: str = "super_admin"
ROLE_TENANT_ADMIN: str = "tenant_admin"
ROLE_EMPLOYEE: str = "employee"

# 文档可见性
DOC_VISIBILITY_PRIVATE: str = "private"
DOC_VISIBILITY_DEPARTMENT: str = "department"
DOC_VISIBILITY_PUBLIC: str = "public"

# 解析任务
PARSE_TASK_MAX_RETRIES: int = 3
PARSE_TASK_RETRY_DELAY_SECONDS: int = 60

# 接口限流
API_RATE_LIMIT_PER_MINUTE: int = 120
