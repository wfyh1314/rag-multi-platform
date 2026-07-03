"""异步批量文档解析、向量化入库、失败重试."""

from typing import Any

from config.constants import PARSE_TASK_MAX_RETRIES, PARSE_TASK_RETRY_DELAY_SECONDS
from tasks.celery_app import celery_app


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
    tenant_id: str,
    user_id: str,
) -> dict[str, Any]:
    """异步任务：解析文档、分块、向量化并入库。"""
    try:
        # TODO: 文档加载 -> 清洗 -> 分块 -> vector_store
        raise NotImplementedError("Parse file task not yet implemented")
    except Exception as exc:
        raise self.retry(exc=exc)
