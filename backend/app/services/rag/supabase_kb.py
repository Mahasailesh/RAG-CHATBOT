from __future__ import annotations

import logging

from openai import OpenAI
from supabase import create_client

from ...core.config import (
    KB_EMBEDDING_MODEL,
    OPENAI_API_KEY,
    SUPABASE_KEY,
    SUPABASE_MATCH_RPC,
    SUPABASE_TABLE,
    SUPABASE_URL,
)
from .errors import KnowledgeBaseError
from .knowledge_base import RetrievedChunk


def _ensure_supabase_env() -> None:
    missing = []
    if not SUPABASE_URL:
        missing.append("CLEARPASS_SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("CLEARPASS_SUPABASE_KEY")
    if missing:
        raise KnowledgeBaseError(f"Missing Supabase configuration: {', '.join(missing)}")


class SupabaseKnowledgeBase:
    def __init__(self, client, openai: OpenAI):
        self._client = client
        self._openai = openai

    @classmethod
    def load(cls) -> "SupabaseKnowledgeBase":
        _ensure_supabase_env()
        if not OPENAI_API_KEY:
            raise KnowledgeBaseError("OpenAI API key is required for embeddings.")
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        openai = OpenAI(api_key=OPENAI_API_KEY)
        return cls(client=client, openai=openai)

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        if not query.strip():
            return []

        try:
            response = self._openai.embeddings.create(
                model=KB_EMBEDDING_MODEL,
                input=[query],
            )
            embedding = response.data[0].embedding
        except Exception as exc:
            raise KnowledgeBaseError("Failed to generate query embedding.") from exc

        payload = {
            "query_embedding": embedding,
            "match_count": top_k,
        }

        try:
            result = self._client.rpc(SUPABASE_MATCH_RPC, payload).execute()
        except Exception as exc:
            raise KnowledgeBaseError("Supabase retrieval failed.") from exc
        if not result.data:
            return []

        chunks: list[RetrievedChunk] = []
        for row in result.data:
            chunks.append(
                RetrievedChunk(
                    source=row.get("source_url") or row.get("document_url") or "supabase",
                    chunk_index=0,
                    text=row.get("content_chunk", ""),
                    score=float(row.get("similarity", 0.0)),
                )
            )
        return chunks


def supabase_ready() -> bool:
    try:
        _ensure_supabase_env()
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = client.table(SUPABASE_TABLE).select("id").limit(1).execute()
        if response.data is not None:
            return True
    except Exception as exc:
        logging.info("Supabase readiness check failed: %s", exc)
    return False
