"""SQLAlchemy / MySQL 异常映射为统一业务错误响应."""

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from config.response_codes import BAD_REQUEST, DATABASE_ERROR

_SCHEMA_ERRNOS = {1054, 1146, 1364}
_CONNECTION_ERRNOS = {2002, 2003, 2006, 2013}


def map_db_exception(exc: SQLAlchemyError) -> tuple[int, int, str]:
    """将数据库异常映射为 (http_status, business_code, user_message)。"""
    if isinstance(exc, IntegrityError):
        errno = _mysql_errno(exc)
        if errno == 1062:
            return 409, BAD_REQUEST, "数据已存在，请勿重复提交"
        return 409, BAD_REQUEST, "数据完整性冲突，请检查后重试"

    if isinstance(exc, OperationalError):
        errno = _mysql_errno(exc)
        if errno in _CONNECTION_ERRNOS:
            return 503, DATABASE_ERROR, "数据库连接失败，请稍后重试或联系管理员"
        if errno in _SCHEMA_ERRNOS:
            return (
                503,
                DATABASE_ERROR,
                "数据库结构不匹配，请重启后端触发自动迁移，或执行 alembic upgrade head",
            )

    return 500, DATABASE_ERROR, "数据库操作失败，请稍后重试"


def _mysql_errno(exc: SQLAlchemyError) -> int | None:
    orig = getattr(exc, "orig", None)
    if orig is None or not getattr(orig, "args", None):
        return None
    first = orig.args[0]
    return first if isinstance(first, int) else None
