import os
import chromadb
from typing import List, Dict, Any
from .embedder import OllamaEmbedder

CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
COLLECTION_NAME = "obsidian_knowledge"

class ObsidianVectorStore:
    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedder = OllamaEmbedder()
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Obsidian Vault Knowledge Base for Student Risk Intervention"}
        )

    def add_document_chunk(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """Add or update a single text chunk with embedding."""
        embedding = self.embedder.get_embedding(text)
        self.collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )

    def search(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Search similar document chunks by query text."""
        query_embedding = self.embedder.get_embedding(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        formatted = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
            for doc, meta, dist in zip(docs, metas, distances):
                formatted.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": dist
                })
        return formatted

    def get_stats(self) -> Dict[str, Any]:
        """Return total chunks count in collection."""
        return {
            "collection_name": COLLECTION_NAME,
            "total_chunks": self.collection.count()
        }
