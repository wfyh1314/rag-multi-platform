"""全局日志持久化."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_LOG_DIR = Path("logs")
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_initialized = False


def setup_logger(
    name: str = "rag",
    level: int = logging.INFO,
    log_file: Optional[str] = "logs/app.log",
) -> logging.Logger:
    """配置并返回带控制台与文件处理器的应用日志器。"""
    global _initialized
    logger = logging.getLogger(name)

    if _initialized:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _initialized = True
    return logger


def get_logger(name: str = "rag") -> logging.Logger:
    """获取日志实例，必要时先初始化。"""
    if not _initialized:
        setup_logger()
    return logging.getLogger(name)
