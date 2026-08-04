"""读取 .env、全局单例 llm/embedding/rerank/redis/qdrant/mysql 配置."""

from functools import lru_cache
from typing import Optional

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从环境变量 / .env 文件加载的应用配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用
    app_name: str = "enterprise_rag"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # 认证
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440
    auth_skip: bool = True

    # 跨域
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5000,http://127.0.0.1:5000"

    # MySQL 数据库
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "rag_user"
    mysql_password: str = "rag_password"
    mysql_database: str = "rag_multi_platform"
    mysql_charset: str = "utf8mb4"

    # Redis 缓存
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    # Qdrant 向量库
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    qdrant_collection_name: str = Field(
        default="knowledge_base",
        validation_alias=AliasChoices("QDRANT_COLLECTION_NAME", "QDRANT_COLLECTION_PREFIX"),
    )

    # Celery 异步任务
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # 阿里通义 DashScope（优先）
    dashscope_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("DASHSCOPE_API_KEY", "LLM_API_KEY", "EMBEDDING_API_KEY"),
    )
    dashscope_api_base: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        validation_alias=AliasChoices("ALI_TONGYI_URL", "LLM_API_BASE", "EMBEDDING_API_BASE"),
    )
    llm_model: str = Field(
        default="qwen-plus",
        validation_alias=AliasChoices("ALI_TONGYI_MAX_MODEL", "LLM_MODEL"),
    )
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    embedding_model: str = Field(
        default="text-embedding-v1",
        validation_alias=AliasChoices("TONGYI_EMBEDDING_MODEL", "EMBEDDING_MODEL"),
    )
    embedding_dimension: int = 1536

    # Rerank（DashScope gte-rerank-v2）
    rerank_api_base: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("RERANK_API_BASE"),
    )
    rerank_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("RERANK_API_KEY"),
    )
    rerank_model: str = Field(
        default="gte-rerank-v2",
        validation_alias=AliasChoices("RERANK_MODEL"),
    )

    # 文档分块
    chunk_size: int = 1000
    chunk_overlap: int = 150
    chunk_strategy: str = Field(default="fixed", description="fixed | semantic")
    semantic_chunk_breakpoint_threshold: float = Field(default=0.5)
    async_upload_threshold_mb: int = Field(default=5)

    # 文件存储
    upload_dir: str = "tmp/uploads"
    max_upload_size_mb: int = Field(default=50)

    # MinerU PDF 解析
    mineru_api_url: Optional[str] = None
    mineru_api_key: Optional[str] = None

    @model_validator(mode="after")
    def _strip_quoted_env_values(self) -> "Settings":
        """去除 .env 中可能带入的多余引号."""
        self.dashscope_api_key = self.dashscope_api_key.strip().strip('"').strip("'")
        self.dashscope_api_base = self.dashscope_api_base.strip().strip('"').strip("'")
        self.llm_model = self.llm_model.strip().strip('"').strip("'")
        self.embedding_model = self.embedding_model.strip().strip('"').strip("'")
        self.rerank_model = self.rerank_model.strip().strip('"').strip("'")
        if self.rerank_api_key:
            self.rerank_api_key = self.rerank_api_key.strip().strip('"').strip("'")
        if self.rerank_api_base:
            self.rerank_api_base = self.rerank_api_base.strip().strip('"').strip("'")
        return self

    @property
    def llm_api_base(self) -> str:
        return self.dashscope_api_base

    @property
    def llm_api_key(self) -> str:
        return self.dashscope_api_key

    @property
    def embedding_api_base(self) -> str:
        return self.dashscope_api_base

    @property
    def embedding_api_key(self) -> str:
        return self.dashscope_api_key

    @property
    def rerank_api_url(self) -> str:
        if self.rerank_api_base:
            return self.rerank_api_base.rstrip("/")
        return "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"

    @property
    def effective_rerank_api_key(self) -> str:
        if self.rerank_api_key:
            return self.rerank_api_key
        return self.dashscope_api_key

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def mysql_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset={self.mysql_charset}"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    """返回缓存的配置单例。"""
    return Settings()


settings = get_settings()
