"""Celery 异步后台任务（大文件解析不阻塞前端）."""

from tasks.celery_app import celery_app

__all__ = ["celery_app"]
