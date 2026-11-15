import hashlib
import math
import re
import httpx
from typing import List

OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIM = 768


class OllamaEmbedder:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = EMBEDDING_MODEL):
        self.base_url = base_url
        self.model = model
        self._ollama_available = None

    def _fallback_embedding(self, text: str, dim: int = EMBEDDING_DIM) -> List[float]:
        """
        Deterministic 768-dim semantic feature hashing fallback (word + char n-grams)
        compatible with nomic-embed-text dimension when Ollama server is offline/slow.
        """
        vec = [0.0] * dim
        clean = text.lower()
        tokens = re.findall(r"\w+", clean, flags=re.UNICODE)
        features = list(tokens)
        # Add bigrams and character trigrams for rich Vietnamese & technical term matching
        for i in range(len(tokens) - 1):
            features.append(f"{tokens[i]}_{tokens[i+1]}")
        for token in tokens:
            if len(token) >= 3:
                for j in range(len(token) - 2):
                    features.append(token[j : j + 3])

        if not features:
            return [1.0 / math.sqrt(dim)] * dim

        for feat in features:
            h = int(hashlib.md5(feat.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if ((h >> 16) & 1) == 0 else -1.0
            weight = 2.0 if "_" in feat or len(feat) > 4 else 1.0
            vec[idx] += sign * weight

        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [round(v / norm, 6) for v in vec]

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for a single text using Ollama nomic-embed-text with fast fallback."""
        if self._ollama_available is False:
            return self._fallback_embedding(text)

        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text
        }
        try:
            with httpx.Client(timeout=2.5) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                emb = data.get("embedding")
                if emb and len(emb) == EMBEDDING_DIM:
                    self._ollama_available = True
                    return emb
        except Exception:
            self._ollama_available = False

        return self._fallback_embedding(text)

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return [self.get_embedding(t) for t in texts]

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute Cosine Similarity between two embedding vectors."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a)) or 1.0
        norm_b = math.sqrt(sum(b * b for b in vec_b)) or 1.0
        return max(0.0, min(1.0, dot / (norm_a * norm_b)))

