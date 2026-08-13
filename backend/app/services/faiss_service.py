import os
import faiss
import numpy as np
from typing import List, Tuple
from app.core.logger import logger

class FAISSService:
    """Service managing FAISS vector index creation, persistence, and nearest neighbor search."""

    def __init__(self, dimension: int = 768, index_path: str = "data/faiss_index.bin"):
        self.dimension = dimension
        self.index_path = index_path
        self.index = None
        self._initialize_index()

    def _initialize_index(self):
        """Loads index from disk if existing, otherwise initializes a new IndexFlatIP."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors from {self.index_path}")
            except Exception as e:
                logger.error(f"Failed to read FAISS index: {e}. Creating new index.")
                self.index = faiss.IndexFlatIP(self.dimension)
        else:
            self.index = faiss.IndexFlatIP(self.dimension)

    def add_vectors(self, vectors: np.ndarray) -> List[int]:
        """Adds normalized 2D numpy vectors to the FAISS index and saves to disk."""
        if vectors.size == 0:
            return []
            
        if vectors.dtype != np.float32:
            vectors = vectors.astype(np.float32)

        start_id = self.index.ntotal
        self.index.add(vectors)
        assigned_ids = list(range(start_id, self.index.ntotal))
        self.save_index()
        return assigned_ids

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> Tuple[List[float], List[int]]:
        """Searches for top_k nearest vectors using Cosine similarity."""
        if self.index.ntotal == 0:
            return [], []

        if query_vector.ndim == 1:
            query_vector = np.expand_dims(query_vector, axis=0)

        if query_vector.dtype != np.float32:
            query_vector = query_vector.astype(np.float32)

        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_vector, k)
        
        scores = distances[0].tolist()
        vector_ids = indices[0].tolist()
        
        return scores, vector_ids

    def save_index(self):
        """Persists the FAISS index to disk."""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            faiss.write_index(self.index, self.index_path)
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def clear(self):
        """Clears the FAISS index."""
        self.index = faiss.IndexFlatIP(self.dimension)
        if os.path.exists(self.index_path):
            try:
                os.remove(self.index_path)
            except OSError as e:
                logger.warning(f"Could not remove FAISS index file '{self.index_path}': {e}")

faiss_service = FAISSService()
