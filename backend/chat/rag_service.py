"""RAG 检索上下文构建."""

from typing import Any, Optional

from config.constants import DEFAULT_RERANK_TOP_N
from file_mgr.file_service import get_accessible_file_record, list_files_for_user
from retrieval.multimodal_retrieval import MultimodalRetrieval
from storage.mysql_db import get_db_session
from storage.repositories.file_tag_repository import FileTagRepository


def _accessible_file_ids(user: dict[str, Any]) -> set[str]:
    return {
        item["file_id"]
        for item in list_files_for_user(user.get("user_id", ""))["files"]
    }


def _build_search_filters(
    user: dict[str, Any],
    file_id: Optional[str],
    tag_ids: Optional[list[str]],
) -> dict[str, Any] | None:
    """构建检索过滤：标签场景先 MySQL 交集 file_id，再 Qdrant _should 过滤。"""
    accessible_ids = _accessible_file_ids(user)
    allowed_ids: set[str] | None = None

    if tag_ids:
        with get_db_session() as session:
            tagged_ids = FileTagRepository(session).list_file_ids_by_tag_ids(tag_ids)
        allowed_ids = accessible_ids & tagged_ids
        if file_id:
            get_accessible_file_record(user, file_id)
            allowed_ids = allowed_ids & {file_id}
        if not allowed_ids:
            return None
        if len(allowed_ids) == 1:
            return {"file_id": next(iter(allowed_ids))}
        return {"_should": [{"file_id": fid} for fid in sorted(allowed_ids)]}

    if file_id:
        get_accessible_file_record(user, file_id)
        return {"file_id": file_id}

    if not accessible_ids:
        return None
    if len(accessible_ids) == 1:
        return {"file_id": next(iter(accessible_ids))}
    return {"_should": [{"file_id": fid} for fid in sorted(accessible_ids)]}


def _format_hit_content(hit: dict[str, Any], index: int) -> str:
    content = hit.get("content", "").strip()
    metadata = hit.get("metadata") or {}
    modality = metadata.get("modality", "text")
    media_path = metadata.get("media_path", "")
    if modality == "image":
        caption = content or "(图片内容)"
        if media_path:
            return f"[{index}] [图片] {caption} (路径: {media_path})"
        return f"[{index}] [图片] {caption}"
    if content:
        return f"[{index}] {content}"
    return ""


def search_rag_hits(
    user: dict[str, Any],
    query: str,
    file_id: Optional[str] = None,
    tag_ids: Optional[list[str]] = None,
    top_k: int = DEFAULT_RERANK_TOP_N,
) -> list[dict[str, Any]]:
    """多模态混合检索 + Rerank，返回命中列表。"""
    search_filters = _build_search_filters(user, file_id, tag_ids)
    if tag_ids and search_filters is None:
        return []
    if not file_id and not tag_ids and search_filters is None:
        return []

    return MultimodalRetrieval().search(
        query,
        top_k=top_k,
        filters=search_filters,
    )


def format_rag_context(hits: list[dict[str, Any]]) -> str:
    """将检索命中格式化为 LLM 上下文。"""
    parts: list[str] = []
    for i, hit in enumerate(hits, start=1):
        line = _format_hit_content(hit, i)
        if line:
            parts.append(line)
    if not parts:
        return ""
    return "以下是从知识库检索到的参考片段：\n\n" + "\n\n".join(parts)


def hits_to_sources(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """将检索命中转为 sources 结构。"""
    return [
        {
            "doc_id": hit.get("id"),
            "content": hit.get("content", ""),
            "metadata": hit.get("metadata", {}),
            "score": hit.get("score"),
        }
        for hit in hits
    ]


def build_rag_context(
    user: dict[str, Any],
    query: str,
    file_id: Optional[str] = None,
    tag_ids: Optional[list[str]] = None,
    top_k: int = DEFAULT_RERANK_TOP_N,
) -> tuple[str, list[dict[str, Any]]]:
    """多模态检索 + Rerank 并格式化为 LLM 上下文。"""
    hits = search_rag_hits(user, query, file_id, tag_ids, top_k=top_k)
    if not hits:
        return "", []
    context = format_rag_context(hits)
    if not context:
        return "", hits
    return context, hits
