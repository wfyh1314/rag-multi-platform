"""PDF 解析：pypdf 逐页提取文本."""

from pathlib import Path

from core.exceptions import FileParseError
from document.loaders.base import BaseLoader, Document


class PDFLoader(BaseLoader):
    """使用 pypdf 解析 PDF 文档."""

    extensions = frozenset({".pdf"})

    def load(self, file_path: Path) -> list[Document]:
        if not file_path.exists():
            raise FileParseError("文件不存在", filename=file_path.name)

        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise FileParseError("缺少 pypdf 依赖", filename=file_path.name) from exc

        try:
            reader = PdfReader(str(file_path))
        except Exception as exc:
            raise FileParseError(f"PDF 解析失败: {exc}", filename=file_path.name) from exc

        documents: list[Document] = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            documents.append(
                Document(
                    content=text,
                    metadata={
                        "source": file_path.name,
                        "file_type": "pdf",
                        "page": page_num,
                    },
                )
            )

        if not documents:
            raise FileParseError("PDF 未提取到文本内容", filename=file_path.name)
        return documents
