"""本地临时文件存储、过期清理."""

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import BinaryIO

from config.settings import get_settings


class FileStorage:
    """本地临时文件存储。"""

    def __init__(self, base_dir: str | None = None):
        cfg = get_settings()
        self.base_dir = Path(base_dir or cfg.upload_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file: BinaryIO, filename: str, subdir: str = "") -> str:
        """保存上传文件并返回绝对路径。"""
        target_dir = self.base_dir / subdir if subdir else self.base_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        with open(target_path, "wb") as f:
            shutil.copyfileobj(file, f)
        return str(target_path)

    def delete(self, file_path: str) -> bool:
        """从存储中删除文件。"""
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False

    def delete_dir(self, subdir: str) -> bool:
        """删除子目录及其全部内容。"""
        target_dir = self.base_dir / subdir if subdir else self.base_dir
        if not target_dir.exists():
            return False
        shutil.rmtree(target_dir)
        return True

    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """删除超过 max_age_hours 的文件，返回删除数量。"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        removed = 0
        for path in self.base_dir.rglob("*"):
            if path.is_file():
                mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    path.unlink()
                    removed += 1
        return removed
