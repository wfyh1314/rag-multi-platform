"""MySQL ORM 封装：租户、用户、文件、会话、审计表 CRUD."""

from contextlib import contextmanager
from typing import Any, Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from config.settings import Settings, get_settings

Base = declarative_base()

_engine = None
_SessionLocal = None


def init_db(settings: Optional[Settings] = None, database_url: Optional[str] = None) -> None:
    """初始化 SQLAlchemy 引擎与会话工厂。"""
    global _engine, _SessionLocal
    cfg = settings or get_settings()
    url = database_url or cfg.mysql_url
    _engine = create_engine(url, pool_pre_ping=True, echo=cfg.debug)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def create_tables() -> None:
    """创建所有 ORM 表（若不存在）。"""
    global _engine
    if _engine is None:
        init_db()
    # 导入模型以注册 metadata
    import storage.models  # noqa: F401

    Base.metadata.create_all(bind=_engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """提供事务性数据库会话。"""
    global _SessionLocal
    if _SessionLocal is None:
        init_db()
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class BaseRepository:
    """CRUD 操作基础仓储（占位）。"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, model: Any, record_id: str) -> Optional[Any]:
        """按主键获取记录。"""
        raise NotImplementedError

    def create(self, model: Any, **kwargs: Any) -> Any:
        """创建新记录。"""
        raise NotImplementedError

    def update(self, instance: Any, **kwargs: Any) -> Any:
        """更新已有记录。"""
        raise NotImplementedError

    def delete(self, instance: Any) -> None:
        """删除记录。"""
        raise NotImplementedError
