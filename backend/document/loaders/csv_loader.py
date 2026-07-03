"""CSV 结构化表格转文本块."""

import csv
from pathlib import Path

from core.exceptions import FileParseError
from document.loaders.base import BaseLoader, Document


class CSVLoader(BaseLoader):
    """将 CSV 按行解析为文本块."""

    extensions = frozenset({".csv", ".CSV"})

    def load(self, file_path: Path) -> list[Document]:
        if not file_path.exists():
            raise FileParseError("文件不存在", filename=file_path.name)

        documents: list[Document] = []
        try:
            with open(file_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise FileParseError("CSV 缺少表头", filename=file_path.name)
                for row_num, row in enumerate(reader, start=2):
                    parts = [f"{k}: {v}" for k, v in row.items() if v]
                    if not parts:
                        continue
                    documents.append(
                        Document(
                            content=", ".join(parts),
                            metadata={
                                "source": file_path.name,
                                "file_type": "csv",
                                "row": row_num,
                            },
                        )
                    )
        except FileParseError:
            raise
        except Exception as exc:
            raise FileParseError(f"CSV 解析失败: {exc}", filename=file_path.name) from exc

        if not documents:
            raise FileParseError("CSV 无有效数据行", filename=file_path.name)
        return documents
