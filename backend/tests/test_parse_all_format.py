"""全格式文件解析测试."""

import csv
from pathlib import Path

import pytest

from core.exceptions import FileParseError
from document.loaders import load_document
from document.loaders.csv_loader import CSVLoader
from document.loaders.office_loader import OfficeLoader


def test_loader_rejects_unsupported_format(tmp_path):
    """不支持的扩展名应抛出 FileParseError。"""
    file_path = tmp_path / "test.xyz"
    file_path.write_text("hello")
    with pytest.raises(FileParseError):
        load_document(file_path)


def test_loader_parses_txt(tmp_path):
    """TXT 文件应正确解析。"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello RAG world", encoding="utf-8")
    docs = load_document(file_path)
    assert len(docs) == 1
    assert "Hello RAG world" in docs[0].content


def test_loader_parses_md(tmp_path):
    """Markdown 文件应正确解析。"""
    file_path = tmp_path / "readme.md"
    file_path.write_text("# Title\n\nSome content.", encoding="utf-8")
    docs = load_document(file_path)
    assert len(docs) == 1
    assert "Title" in docs[0].content


def test_loader_parses_csv(tmp_path):
    """CSV 文件应按行生成文本块。"""
    file_path = tmp_path / "data.csv"
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "age"])
        writer.writeheader()
        writer.writerow({"name": "Alice", "age": "30"})
        writer.writerow({"name": "Bob", "age": "25"})

    docs = CSVLoader().load(file_path)
    assert len(docs) == 2
    assert "Alice" in docs[0].content
    assert "Bob" in docs[1].content


def test_loader_parses_csv_uppercase_extension(tmp_path):
    """CSV 加载器应支持 .CSV 扩展名。"""
    file_path = tmp_path / "data.CSV"
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name"])
        writer.writeheader()
        writer.writerow({"name": "Test"})

    docs = load_document(file_path)
    assert len(docs) == 1
    assert "Test" in docs[0].content


def test_loader_rejects_doc_format(tmp_path):
    """旧版 .doc 格式应抛出 FileParseError。"""
    file_path = tmp_path / "legacy.doc"
    file_path.write_bytes(b"fake doc content")
    with pytest.raises(FileParseError, match="docx"):
        OfficeLoader().load(file_path)


def test_load_document_returns_document_objects(tmp_path):
    """load_document 应返回 Document 实例。"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("document test", encoding="utf-8")
    docs = load_document(file_path)
    from document.loaders.base import Document

    assert isinstance(docs[0], Document)
    assert docs[0].content == "document test"
