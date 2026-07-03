"""文档分块."""

from document.chunkers.splitter import (
    split_by_fixed_length,
    split_document,
    split_semantic,
)

__all__ = ["split_by_fixed_length", "split_document", "split_semantic"]
