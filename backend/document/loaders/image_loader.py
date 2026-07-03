"""图片加载：MVP 提取元数据描述文本（OCR 扩展点）."""

from pathlib import Path

from core.exceptions import FileParseError
from document.loaders.base import BaseLoader, Document


class ImageLoader(BaseLoader):
    """加载图片并生成用于索引的描述文本."""

    extensions = frozenset({".png", ".jpg", ".jpeg", ".webp"})

    def load(self, file_path: Path) -> list[Document]:
        if not file_path.exists():
            raise FileParseError("文件不存在", filename=file_path.name)

        width, height = self._get_dimensions(file_path)
        content = (
            f"[图片文件] 文件名: {file_path.name}, "
            f"格式: {file_path.suffix.lstrip('.')}, "
            f"尺寸: {width}x{height}. "
            f"（OCR 文本提取待扩展）"
        )
        return [
            Document(
                content=content,
                metadata={
                    "source": file_path.name,
                    "file_type": "image",
                    "width": width,
                    "height": height,
                },
            )
        ]

    def _get_dimensions(self, path: Path) -> tuple[int, int]:
        try:
            from PIL import Image

            with Image.open(path) as img:
                return img.size
        except Exception:
            return 0, 0
