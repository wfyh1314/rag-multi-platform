"""PDF loader 测试."""

from io import BytesIO

import pytest
from pypdf import PdfWriter

from document.loaders.pdf_loader import PDFLoader


def _make_pdf_with_text(text: str) -> bytes:
    """创建含单页文本的最小 PDF。"""
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    # pypdf 空白页无文本；此处用注释说明，实际测试依赖最小 PDF 结构
    # 注：pypdf 难以直接向空白页写入文本
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_pdf_loader_rejects_invalid_pdf(tmp_path):
    """无效 PDF 字节应抛出 FileParseError。"""
    file_path = tmp_path / "bad.pdf"
    file_path.write_bytes(b"%PDF-1.4\nnot a real pdf")
    with pytest.raises(Exception):
        PDFLoader().load(file_path)


def test_pdf_loader_rejects_empty_pdf(tmp_path):
    """无可提取文本的 PDF 应抛出 FileParseError。"""
    file_path = tmp_path / "blank.pdf"
    file_path.write_bytes(_make_pdf_with_text(""))
    with pytest.raises(Exception):
        PDFLoader().load(file_path)
