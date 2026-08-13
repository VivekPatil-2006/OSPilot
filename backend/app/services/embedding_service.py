import hashlib
import re
import httpx
import numpy as np
from typing import List, Optional
from app.core.config import settings
from app.core.logger import logger

import time
from concurrent.futures import ThreadPoolExecutor

class NomicEmbeddingService:
    """Service generating vector embeddings using local Ollama model 'nomic-embed-text'."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.DEFAULT_EMBEDDING_MODEL
        self.vector_dim = 768
        
        # 1. Reusable HTTPX Client with 60s timeout
        self.client = httpx.Client(timeout=60.0)
        self._last_health_check = 0.0
        self._cached_available = False

    def is_available(self) -> bool:
        """Checks Ollama embedding availability dynamically with a 15-second TTL."""
        now = time.time()
        if now - self._last_health_check < 15.0:
            return self._cached_available

        self._last_health_check = now
        try:
            resp = self.client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": "health_check"},
                timeout=3.0
            )
            self._cached_available = (resp.status_code == 200 and len(resp.json().get("embedding", [])) == self.vector_dim)
        except Exception:
            self._cached_available = False

        return self._cached_available

    def get_embedding(self, text: str) -> np.ndarray:
        """Generates a 768-dimensional normalized float32 vector embedding for given text."""
        if self.is_available():
            try:
                response = self.client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                    timeout=5.0
                )

                if response.status_code == 200:
                    data = response.json()
                    embedding = data.get("embedding", [])
                    if len(embedding) == self.vector_dim:
                        vec = np.array(embedding, dtype=np.float32)
                        norm = np.linalg.norm(vec)
                        return vec / (norm + 1e-10)
            except Exception as e:
                logger.warning(f"Embedding request failed: {e}")

        return self._generate_fallback_embedding(text)

    def get_embeddings_batch(self, texts: List[str], max_workers: int = 6) -> np.ndarray:
        """Generates vector embeddings concurrently using ThreadPoolExecutor or fast vector hashing."""
        if not texts:
            return np.empty((0, self.vector_dim), dtype=np.float32)

        t_start = time.time()
        vectors = []

        if self.is_available():
            try:
                embed_resp = self.client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": texts},
                    timeout=10.0
                )
                if embed_resp.status_code == 200:
                    batch_embeddings = embed_resp.json().get("embeddings", [])
                    if len(batch_embeddings) == len(texts):
                        vecs = [np.array(e, dtype=np.float32) / (np.linalg.norm(e) + 1e-10) for e in batch_embeddings]
                        elapsed_ms = round((time.time() - t_start) * 1000, 2)
                        logger.info(f"Ollama True Batch API generated {len(texts)} embeddings in {elapsed_ms}ms")
                        return np.vstack(vecs)
            except Exception:
                pass

            try:
                logger.info(f"Generating {len(texts)} embeddings in parallel with {max_workers} ThreadPool workers...")
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    vectors = list(executor.map(self.get_embedding, texts))
            except Exception as e:
                logger.warning(f"Parallel embedding failed: {e}. Falling back to vector hashing.")
                vectors = [self._generate_fallback_embedding(t) for t in texts]
        else:
            vectors = [self._generate_fallback_embedding(t) for t in texts]

        if not vectors or len(vectors) != len(texts):
            vectors = [self._generate_fallback_embedding(t) for t in texts]

        elapsed_ms = round((time.time() - t_start) * 1000, 2)
        logger.info(f"[Embedding Generation Complete] Processed {len(texts)} text chunks in {elapsed_ms}ms (Avg {round(elapsed_ms/max(len(texts),1), 2)}ms/chunk)")
        return np.vstack(vectors)

    def _generate_fallback_embedding(self, text: str) -> np.ndarray:
        """Deterministic 768-dimensional feature vector hashing tokens and 3-grams for offline matching."""
        vec = np.zeros(self.vector_dim, dtype=np.float32)
        clean_text = text.lower().strip()
        words = re.findall(r'[a-zA-Z0-9]+', clean_text)
        
        for word in words:
            if len(word) < 2:
                continue
            # Word token hash
            h_val = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            idx = h_val % self.vector_dim
            vec[idx] += 3.0
            
            # Substring 3-gram hashes for subword matching
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    ngram = word[i:i+3]
                    n_hash = int(hashlib.md5(ngram.encode('utf-8')).hexdigest(), 16)
                    vec[n_hash % self.vector_dim] += 0.5

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

embedding_service = NomicEmbeddingService()
