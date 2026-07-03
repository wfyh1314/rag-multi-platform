"""内置检索工具，无复杂工具审查."""

from typing import Any


def retrieval_tool(query: str, tenant_id: str, top_k: int = 10) -> list[dict[str, Any]]:
    """LangGraph Agent 内置检索工具。"""
    raise NotImplementedError
