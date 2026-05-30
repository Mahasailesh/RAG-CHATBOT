from __future__ import annotations

from functools import lru_cache

from ...core.config import KB_PROVIDER, KB_QUERY_MAX_CHARS, RETRIEVAL_TOP_K, SUPABASE_KEY, SUPABASE_URL
from ...models import DocumentText
from .knowledge_base import KnowledgeBase, RetrievedChunk
from .supabase_kb import SupabaseKnowledgeBase


@lru_cache(maxsize=1)
def _get_kb():
    provider = KB_PROVIDER
    if provider == "auto":
        if SUPABASE_URL and SUPABASE_KEY:
            return SupabaseKnowledgeBase.load()
        return KnowledgeBase.load()
    if provider == "supabase":
        return SupabaseKnowledgeBase.load()
    return KnowledgeBase.load()


def _build_query(payload: DocumentText) -> str:
    parts: list[str] = []
    remaining = KB_QUERY_MAX_CHARS
    for page_number in sorted(payload.pages.keys()):
        if remaining <= 0:
            break
        page_text = payload.pages[page_number]
        snippet = page_text[:remaining]
        parts.append(f"[Page {page_number}] {snippet}")
        remaining -= len(snippet)
    return "\n".join(parts)


def retrieve_context(payload: DocumentText, top_k: int | None = None) -> list[RetrievedChunk]:
    kb = _get_kb()
    query = _build_query(payload)
    return kb.search(query, top_k or RETRIEVAL_TOP_K)


def format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return ""
    formatted: list[str] = []
    for chunk in chunks:
        formatted.append(
            f"[Source: {chunk.source} | Chunk {chunk.chunk_index}] {chunk.text}"
        )
    return "\n\n".join(formatted)
