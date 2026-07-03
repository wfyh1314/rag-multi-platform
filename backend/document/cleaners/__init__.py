"""文档清洗."""

from document.cleaners.cleaner import (
    clean_document,
    deduplicate_paragraphs,
    remove_empty_lines,
    remove_watermarks,
)

__all__ = [
    "clean_document",
    "deduplicate_paragraphs",
    "remove_empty_lines",
    "remove_watermarks",
]
