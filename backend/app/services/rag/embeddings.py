from __future__ import annotations

from functools import lru_cache

import numpy as np

from ...core.config import EMBEDDING_MODEL
from .errors import KnowledgeBaseError


@lru_cache(maxsize=1)
def _load_embedder(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise KnowledgeBaseError("sentence-transformers is not installed.") from exc
    return SentenceTransformer(model_name)


def embed_texts(texts: list[str], model_name: str | None = None) -> np.ndarray:
    name = model_name or EMBEDDING_MODEL
    model = _load_embedder(name)
    embeddings = model.encode(texts, normalize_embeddings=True)
    return np.asarray(embeddings, dtype="float32")
