"""文档加载与格式解析."""

from pathlib import Path

from core.exceptions import FileParseError
from document.loaders.base import BaseLoader, Document
from document.loaders.csv_loader import CSVLoader
from document.loaders.image_loader import ImageLoader
from document.loaders.office_loader import OfficeLoader
from document.loaders.pdf_loader import PDFLoader

_LOADERS: list[BaseLoader] = [
    PDFLoader(),
    OfficeLoader(),
    CSVLoader(),
    ImageLoader(),
]


def load_document(file_path: str | Path) -> list[Document]:
    """按文件后缀路由到对应 Loader 并加载文档."""
    path = Path(file_path)
    ext = path.suffix.lower()
    for loader in _LOADERS:
        if ext in {e.lower() for e in loader.extensions}:
            return loader.load(path)
    raise FileParseError(f"不支持的文件格式: {ext}")


__all__ = [
    "BaseLoader",
    "CSVLoader",
    "Document",
    "ImageLoader",
    "OfficeLoader",
    "PDFLoader",
    "load_document",
]
