"""图文联合检索，图片/文本统一向量空间."""

from typing import Any, Optional


class MultimodalRetrieval:
    """图文统一向量空间的多模态检索。"""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def search(
        self,
        query: str,
        top_k: int = 10,
        modality: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """在统一向量空间中检索文本与图片。"""
        raise NotImplementedError
