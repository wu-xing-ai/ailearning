"""Embedding service using sentence-transformers + ChromaDB.

Generates vector embeddings for document chunks and supports
semantic similarity search.
"""

import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_data")
COLLECTION_NAME = "document_chunks"

# Prefer Chinese-optimized model, fall back to multilingual
MODEL_CANDIDATES = [
    "shibing624/text2vec-base-chinese",
    "paraphrase-multilingual-MiniLM-L12-v2",
]


class EmbeddingService:
    def __init__(self):
        self._model = None
        self._chroma_client = None
        self._collection = None
        self._model_name = ""

    def _get_model(self):
        if self._model is not None:
            return self._model
        from sentence_transformers import SentenceTransformer

        for candidate in MODEL_CANDIDATES:
            try:
                self._model = SentenceTransformer(candidate)
                self._model_name = candidate
                logger.info(f"Loaded embedding model: {candidate}")
                return self._model
            except Exception as e:
                logger.warning(f"Failed to load model {candidate}: {e}")
                continue
        raise RuntimeError("无法加载任何嵌入模型")

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        import chromadb

        os.makedirs(CHROMA_DIR, exist_ok=True)
        self._chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        self._collection = self._chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    def generate_embedding(self, text: str) -> List[float]:
        model = self._get_model()
        return model.encode(text, show_progress_bar=False).tolist()

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        return model.encode(texts, show_progress_bar=False, batch_size=32).tolist()

    def index_document_chunks(self, doc_id: str, chunks: list) -> int:
        """Index all chunks of a document into ChromaDB.

        Args:
            doc_id: Document ID
            chunks: List of objects with .index (int) and .text (str) attributes

        Returns:
            Number of indexed chunks
        """
        if not chunks:
            return 0

        texts = [ch.text for ch in chunks]
        embeddings = self.generate_embeddings_batch(texts)

        ids = [f"{doc_id}_{ch.index}" for ch in chunks]
        metadatas = [{"doc_id": doc_id, "chunk_index": ch.index} for ch in chunks]

        collection = self._get_collection()

        # Delete existing entries for this doc first
        try:
            existing = collection.get(where={"doc_id": doc_id})
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception:
            pass

        collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        return len(ids)

    def search(self, query: str, top_k: int = 10, doc_ids: Optional[List[str]] = None) -> List[Dict]:
        """Semantic search.

        Returns list of dicts with chunk_id, doc_id, text, score, chunk_index.
        """
        query_embedding = self.generate_embedding(query)
        collection = self._get_collection()

        where_filter = None
        if doc_ids:
            where_filter = {"doc_id": {"$in": doc_ids}}

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()) if collection.count() > 0 else 1,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        items = []
        if not results or not results["ids"] or not results["ids"][0]:
            return items

        for i, chunk_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            dist = results["distances"][0][i] if results["distances"] else 0
            # cosine distance -> similarity: 1 - distance
            score = round(1 - dist, 4)
            items.append({
                "chunk_id": chunk_id,
                "doc_id": meta.get("doc_id", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "text": results["documents"][0][i] if results["documents"] else "",
                "score": score,
            })

        return items

    def delete_document(self, doc_id: str):
        """Remove all chunks of a document from ChromaDB."""
        collection = self._get_collection()
        try:
            existing = collection.get(where={"doc_id": doc_id})
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception:
            pass

    def get_stats(self) -> Dict:
        """Return embedding service status."""
        try:
            model_name = self._model_name or "未加载"
            count = self._get_collection().count() if self._collection or True else 0
            return {
                "model_name": model_name,
                "collection_count": count,
                "status": "ready",
            }
        except Exception as e:
            return {
                "model_name": "未加载",
                "collection_count": 0,
                "status": f"unavailable: {str(e)}",
            }


# Global singleton
embedding_service = EmbeddingService()
