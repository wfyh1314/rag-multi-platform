"""FastAPI 入口：跨域、JWT 全局鉴权、路由挂载、静态托管."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api import audit_router, chat_router, file_router, tenant_router, user_router
from config.settings import get_settings
from core.exceptions import AppError
from core.logger import setup_logger
from core.security import jwt_auth_middleware

settings = get_settings()
logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动与关闭。"""
    logger.info("Starting %s [%s]", settings.app_name, settings.app_env)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title="企业级多租户知识库问答平台",
    description="企业级多租户 RAG 后端 API",
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

# JWT 鉴权中间件
app.middleware("http")(jwt_auth_middleware)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """处理自定义应用异常。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


# 挂载 API 路由
app.include_router(user_router, prefix="/api", tags=["user"])
app.include_router(tenant_router, prefix="/api", tags=["tenant"])
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
