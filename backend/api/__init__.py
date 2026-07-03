"""FastAPI 接口层（仅调度，无复杂业务逻辑）."""

from api.audit_api import router as audit_router
from api.chat_api import router as chat_router
from api.file_api import router as file_router
from api.tenant_api import router as tenant_router
from api.user_api import router as user_router

__all__ = [
    "audit_router",
    "chat_router",
    "file_router",
    "tenant_router",
    "user_router",
]
