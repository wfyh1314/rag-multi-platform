"""FastAPI 入口：跨域、JWT 全局鉴权、路由挂载、静态托管."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api import audit_router, chat_router, file_router, tag_router, user_router
from config.settings import get_settings
from core.exceptions import AppError
from core.logger import setup_logger
from core.rate_limit import RateLimitMiddleware
from core.request_context import RequestUuidMiddleware
from core.response import fail, fail_from_http_status
from core.security import JwtAuthMiddleware
from storage.db_bootstrap import seed_default_data

settings = get_settings()
logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动与关闭。"""
    logger.info("Starting %s [%s]", settings.app_name, settings.app_env)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)
    try:
        seed_default_data(settings)
    except Exception as exc:
        logger.warning("Database bootstrap skipped or failed: %s", exc)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title="企业级知识库问答平台",
    description="企业级 RAG 后端 API",
    version="0.1.0",
    lifespan=lifespan,
)

# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT 鉴权（先注册，后执行）
app.add_middleware(JwtAuthMiddleware)

# API 限流（Redis 不可用时自动跳过）
app.add_middleware(RateLimitMiddleware)

# 请求 UUID（最后注册，最先执行）
app.add_middleware(RequestUuidMiddleware)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """处理自定义应用异常。"""
    request_uuid = getattr(request.state, "uuid", "") or ""
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(
            code=exc.code,
            message=exc.message,
            description=exc.description,
            request_uuid=request_uuid,
        ),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理 HTTP 异常。"""
    request_uuid = getattr(request.state, "uuid", "") or ""
    detail = exc.detail
    message = detail if isinstance(detail, str) else str(detail)
    description = ""
    if isinstance(detail, list):
        message = "; ".join(
            item.get("msg", str(item)) if isinstance(item, dict) else str(item)
            for item in detail
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=fail_from_http_status(
            status_code=exc.status_code,
            message=message,
            description=description,
            request_uuid=request_uuid,
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """处理请求参数校验异常。"""
    request_uuid = getattr(request.state, "uuid", "") or ""
    errors = exc.errors()
    message = "; ".join(
        f"{'.'.join(str(loc) for loc in err.get('loc', []))}: {err.get('msg', '')}"
        for err in errors
    )
    return JSONResponse(
        status_code=422,
        content=fail_from_http_status(
            status_code=422,
            message=message or "参数校验失败",
            description="参数校验失败",
            result=errors,
            request_uuid=request_uuid,
        ),
    )


# 挂载 API 路由
app.include_router(user_router, prefix="/api", tags=["user"])
app.include_router(tag_router, prefix="/api", tags=["tag"])
app.include_router(file_router, prefix="/api", tags=["file"])
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(audit_router, prefix="/api", tags=["audit"])

# 静态文件（可选前端资源）
_static_dir = Path("static")
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """健康检查接口。"""
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
