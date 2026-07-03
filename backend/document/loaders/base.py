"""Loader 抽象基类与 Document 数据结构."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Document:
    """加载器返回的文档单元，含正文与元数据."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseLoader(ABC):
    """所有格式加载器的抽象基类。每个子类负责一种文件格式."""

    @abstractmethod
    def load(self, file_path: Path) -> list[Document]:
        """加载文件，返回附带元数据的 Document 列表."""
