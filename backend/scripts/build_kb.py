from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import (
    EMBEDDING_MODEL,
    KB_CHUNK_OVERLAP,
    KB_CHUNK_SIZE,
    KB_INDEX_DIR,
    KB_INDEX_PATH,
    KB_META_PATH,
    KB_SOURCE_DIR,
)
from app.services.rag.chunker import chunk_text
from app.services.rag.embeddings import embed_texts
from app.services.rag.errors import KnowledgeBaseError


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise KnowledgeBaseError("pypdf is required to ingest PDF files.") from exc

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_documents(source_dir: Path) -> list[tuple[str, str]]:
    documents: list[tuple[str, str]] = []
    for path in source_dir.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            text = _read_text(path)
        elif suffix == ".pdf":
            text = _read_pdf(path)
        else:
            continue
        if text.strip():
            documents.append((str(path), text))
    return documents


def build_index(source_dir: Path, index_dir: Path) -> None:
    documents = _load_documents(source_dir)
    if not documents:
        raise KnowledgeBaseError("No documents found to ingest.")

    chunks: list[str] = []
    metadata: list[dict] = []
    for source, text in documents:
        for chunk_index, chunk in enumerate(
            chunk_text(text, KB_CHUNK_SIZE, KB_CHUNK_OVERLAP)
        ):
            metadata.append(
                {"source": source, "chunk_index": chunk_index, "text": chunk}
            )
            chunks.append(chunk)

    embeddings = embed_texts(chunks, EMBEDDING_MODEL)
    dim = embeddings.shape[1]
    try:
        import faiss
    except ImportError as exc:
        raise KnowledgeBaseError("faiss-cpu is required to build the index.") from exc

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    index_dir.mkdir(parents=True, exist_ok=True)
    index_path = index_dir / "index.faiss"
    meta_path = index_dir / "metadata.json"
    faiss.write_index(index, str(index_path))
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FAISS knowledge base index.")
    parser.add_argument("--source", type=Path, default=KB_SOURCE_DIR)
    parser.add_argument("--out", type=Path, default=KB_INDEX_DIR)
    args = parser.parse_args()

    build_index(args.source, args.out)


if __name__ == "__main__":
    main()
