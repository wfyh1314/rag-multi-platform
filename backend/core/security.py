"""密码加密、Token生成、接口鉴权中间件."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import Settings, get_settings
from core.exceptions import AuthenticationError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer(auto_error=False)

# 生产环境跳过鉴权的路径（健康检查、文档）
PUBLIC_PATHS = frozenset({"/health", "/docs", "/openapi.json", "/redoc"})


def hash_password(plain_password: str) -> str:
    """使用 bcrypt 哈希明文密码。"""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    settings: Optional[Settings] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """创建 JWT 访问令牌。"""
    cfg = settings or get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=cfg.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, cfg.jwt_secret_key, algorithm=cfg.jwt_algorithm)


def decode_access_token(token: str, settings: Optional[Settings] = None) -> dict[str, Any]:
    """解码并校验 JWT 访问令牌。"""
    cfg = settings or get_settings()
    try:
        return jwt.decode(token, cfg.jwt_secret_key, algorithms=[cfg.jwt_algorithm])
    except JWTError as exc:
        raise AuthenticationError("Token 无效或已过期") from exc


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """FastAPI 依赖：从 JWT 提取当前用户。"""
    if settings.auth_skip:
        return {"user_id": "dev-user", "tenant_id": "dev-tenant", "role": "tenant_admin"}

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials, settings)
    return {
        "user_id": payload.get("sub"),
        "tenant_id": payload.get("tenant_id"),
        "role": payload.get("role"),
    }


async def jwt_auth_middleware(request: Request, call_next):
    """JWT 鉴权中间件，保护需认证的路由。"""
    settings = get_settings()
    path = request.url.path

    if path in PUBLIC_PATHS or settings.auth_skip:
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权访问")

    token = auth_header.split(" ", 1)[1]
    decode_access_token(token, settings)
    return await call_next(request)
