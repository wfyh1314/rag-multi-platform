"""异步批量文档解析、向量化入库、失败重试."""

from typing import Any

from config.constants import PARSE_TASK_MAX_RETRIES, PARSE_TASK_RETRY_DELAY_SECONDS
from core.logger import get_logger
from document.pipeline import DocumentProcessor
from storage.mysql_db import get_db_session
from storage.repositories.file_repository import FileRepository
from tag.tag_service import TagService
from tasks.celery_app import celery_app

logger = get_logger()


@celery_app.task(
    bind=True,
    max_retries=PARSE_TASK_MAX_RETRIES,
    default_retry_delay=PARSE_TASK_RETRY_DELAY_SECONDS,
    name="tasks.parse_file",
)
def parse_file_task(
    self,
    file_id: str,
    file_path: str,
    user_id: str,
    visibility: str = "private",
) -> dict[str, Any]:
    """异步任务：解析文档、分块、向量化并入库。"""
    try:
        with get_db_session() as session:
            repo = FileRepository(session)
            record = repo.get_by_id(file_id)
            if record:
                record.status = "parsing"
                session.flush()

        processor = DocumentProcessor()
        result = processor.process(
            file_path=file_path,
            file_id=file_id,
            user_id=user_id,
            visibility=visibility,
        )

        tag_service = TagService()
        try:
            tag_service.auto_tag_file(file_id, file_path)
        except Exception as exc:
            logger.warning("异步任务自动打标失败 file_id=%s: %s", file_id, exc)

        with get_db_session() as session:
            repo = FileRepository(session)
            record = repo.get_by_id(file_id)
            if record:
                record.status = result["status"]
                record.chunk_count = result["chunk_count"]
                record.message = result.get("message")
                session.flush()

        return result
    except Exception as exc:
        with get_db_session() as session:
            repo = FileRepository(session)
            record = repo.get_by_id(file_id)
            if record:
                record.status = "failed"
                record.message = str(exc)[:512]
                session.flush()
        raise self.retry(exc=exc)
