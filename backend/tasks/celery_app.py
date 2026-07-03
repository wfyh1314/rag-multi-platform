"""Celery 实例、队列配置."""

from celery import Celery

from config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "enterprise_multi_tenant_rag",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["tasks.parse_file_task"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
