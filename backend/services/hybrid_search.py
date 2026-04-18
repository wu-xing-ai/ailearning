"""Hybrid search combining keyword (SQL LIKE) and semantic (vector) results.

Uses Reciprocal Rank Fusion (RRF) to merge results.
"""

import re
from typing import Dict, List, Optional

from services.embedding_service import embedding_service


def _keyword_search(db, query: str, top_k: int = 10, doc_ids: Optional[List[str]] = None) -> List[Dict]:
    """SQL LIKE search on document_chunks.text."""
    from models.document_chunk import DocumentChunk
    from models.document import Document as DocumentModel
    from sqlalchemy import or_

    search_term = f"%{query}%"
    q = db.query(DocumentChunk, DocumentModel.filename, DocumentModel.file_type).join(
        DocumentModel, DocumentChunk.document_id == DocumentModel.id
    ).filter(DocumentChunk.text.like(search_term))

    if doc_ids:
        q = q.filter(DocumentChunk.document_id.in_(doc_ids))

    rows = q.limit(top_k).all()

    results = []
    for chunk, filename, file_type in rows:
        snippet = _make_snippet(chunk.text, query, 100)
        results.append({
            "doc_id": chunk.document_id,
            "filename": filename,
            "file_type": file_type,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
            "score": 1.0,
            "snippet": snippet,
            "source": "keyword",
        })
    return results


def _semantic_search(query: str, top_k: int = 10, doc_ids: Optional[List[str]] = None) -> List[Dict]:
    """Vector similarity search via ChromaDB."""
    items = embedding_service.search(query, top_k=top_k, doc_ids=doc_ids)
    results = []
    for item in items:
        results.append({
            "doc_id": item["doc_id"],
            "filename": "",
            "file_type": "",
            "chunk_index": item["chunk_index"],
            "text": item["text"],
            "score": item["score"],
            "snippet": _make_snippet(item["text"], query, 100),
            "source": "semantic",
        })
    return results


def _reciprocal_rank_fusion(
    keyword_results: List[Dict],
    semantic_results: List[Dict],
    k: int = 60,
) -> List[Dict]:
    """Merge results using RRF."""
    scores: Dict[str, float] = {}
    data: Dict[str, Dict] = {}

    for rank, item in enumerate(keyword_results):
        key = f"{item['doc_id']}_{item['chunk_index']}"
        scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
        if key not in data:
            data[key] = {**item, "source": "hybrid"}

    for rank, item in enumerate(semantic_results):
        key = f"{item['doc_id']}_{item['chunk_index']}"
        scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
        if key not in data:
            data[key] = {**item, "source": "hybrid"}
        else:
            # Merge: keep keyword filename/file_type if available
            if item.get("filename") and not data[key].get("filename"):
                data[key]["filename"] = item["filename"]
            if item.get("file_type") and not data[key].get("file_type"):
                data[key]["file_type"] = item["file_type"]

    ranked = sorted(data.items(), key=lambda x: scores[x[0]], reverse=True)
    for key, item in ranked:
        item["score"] = round(scores[key], 6)
    return [item for _, item in ranked]


def _make_snippet(text: str, query: str, max_len: int = 100) -> str:
    """Extract a snippet around the first match of query in text."""
    if not text:
        return ""
    lower = text.lower()
    q_lower = query.lower()
    idx = lower.find(q_lower)
    if idx == -1:
        return text[:max_len] + ("..." if len(text) > max_len else "")
    start = max(0, idx - 30)
    end = min(len(text), idx + len(query) + 70)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet += "..."
    return snippet


def hybrid_search(
    db,
    query: str,
    mode: str = "hybrid",
    top_k: int = 10,
    doc_ids: Optional[List[str]] = None,
) -> Dict:
    """Perform search in specified mode.

    Args:
        db: SQLAlchemy session
        query: Search query string
        mode: "keyword", "semantic", or "hybrid"
        top_k: Max results
        doc_ids: Optional filter by document IDs

    Returns:
        Dict with results, mode, total count
    """
    if mode == "keyword":
        results = _keyword_search(db, query, top_k, doc_ids)
    elif mode == "semantic":
        results = _semantic_search(query, top_k, doc_ids)
        # Enrich with filename from DB
        _enrich_filenames(db, results)
    else:
        kw = _keyword_search(db, query, top_k, doc_ids)
        sem = _semantic_search(query, top_k, doc_ids)
        results = _reciprocal_rank_fusion(kw, sem)[:top_k]

    return {
        "results": results[:top_k],
        "mode": mode,
        "total": len(results),
    }


def _enrich_filenames(db, results: List[Dict]):
    """Fill in filename and file_type from database for semantic results."""
    from models.document import Document as DocumentModel

    doc_ids = list(set(r["doc_id"] for r in results if r["doc_id"] and not r["filename"]))
    if not doc_ids:
        return
    docs = db.query(DocumentModel).filter(DocumentModel.id.in_(doc_ids)).all()
    doc_map = {d.id: d for d in docs}
    for r in results:
        if not r["filename"] and r["doc_id"] in doc_map:
            r["filename"] = doc_map[r["doc_id"]].filename
            r["file_type"] = doc_map[r["doc_id"]].file_type
