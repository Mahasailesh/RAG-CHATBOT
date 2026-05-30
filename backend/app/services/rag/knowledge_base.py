from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from ...core.config import (
    EMBEDDING_MODEL,
    KB_INDEX_PATH,
    KB_META_PATH,
    KB_PROVIDER,
    SUPABASE_KEY,
    SUPABASE_URL,
)
from .embeddings import embed_texts
from .errors import KnowledgeBaseError


@dataclass
class RetrievedChunk:
    source: str
    chunk_index: int
    text: str
    score: float


class KnowledgeBase:
    def __init__(self, index, metadata: list[dict], model_name: str):
        self._index = index
        self._metadata = metadata
        self._model_name = model_name

    @classmethod
    def load(cls, index_path: Path | None = None, meta_path: Path | None = None):
        idx_path = index_path or KB_INDEX_PATH
        meta = meta_path or KB_META_PATH

        if not idx_path.exists() or not meta.exists():
            raise KnowledgeBaseError("Knowledge base index not found. Build it first.")

        try:
            import faiss
        except ImportError as exc:
            raise KnowledgeBaseError("faiss-cpu is not installed.") from exc

        index = faiss.read_index(str(idx_path))
        metadata = meta.read_text(encoding="utf-8")
        records = json.loads(metadata)
        return cls(index=index, metadata=records, model_name=EMBEDDING_MODEL)

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        if not query.strip():
            return []
        embeddings = embed_texts([query], self._model_name)
        distances, indices = self._index.search(embeddings, top_k)
        results: list[RetrievedChunk] = []
        for score, idx in zip(distances[0].tolist(), indices[0].tolist()):
            if idx < 0 or idx >= len(self._metadata):
                continue
            record = self._metadata[idx]
            results.append(
                RetrievedChunk(
                    source=record.get("source", "unknown"),
                    chunk_index=record.get("chunk_index", 0),
                    text=record.get("text", ""),
                    score=float(score),
                )
            )
        return results


def kb_ready(index_path: Path | None = None, meta_path: Path | None = None) -> bool:
    if KB_PROVIDER == "supabase":
        from .supabase_kb import supabase_ready

        return supabase_ready()
    if KB_PROVIDER == "auto" and SUPABASE_URL and SUPABASE_KEY:
        from .supabase_kb import supabase_ready

        return supabase_ready()
    idx_path = index_path or KB_INDEX_PATH
    meta = meta_path or KB_META_PATH
    return idx_path.exists() and meta.exists()
