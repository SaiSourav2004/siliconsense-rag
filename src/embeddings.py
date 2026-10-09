from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        # The model is loaded once on initialization
        self.model = SentenceTransformer(self.model_name)
        
    def get_dimension(self) -> int:
        """Programmatically return the embedding dimension."""
        return self.model.get_embedding_dimension()
        
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Embed a list of texts in batches.
        Returns a list of float lists compatible with ChromaDB.
        """
        if not texts:
            return []
            
        # sentence-transformers automatically handles batching if batch_size is provided
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=False # Keep standard output unless cosine strictly requires it
        )
        return embeddings.tolist()
