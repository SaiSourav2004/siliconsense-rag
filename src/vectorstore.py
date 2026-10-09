import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any

class VectorStore:
    def __init__(self, persist_dir: str, collection_name: str = "chipmatch_chunks"):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        
        # Ensure directory exists
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize ChromaDB client with persistent local storage
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "ChipMatch-RAG chunk embeddings"}
        )
        
    def add_chunks(self, ids: List[str], documents: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]):
        """
        Add chunks to ChromaDB safely. 
        Ignores duplicates based on 'ids' (idempotent).
        """
        if not ids:
            return
            
        # ChromaDB's add method will raise an error if IDs already exist.
        # We can either use upsert or check existing. We'll use upsert to be safe/idempotent.
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
    def get_count(self) -> int:
        """Return the number of records in the collection."""
        return self.collection.count()
        
    def search(self, query_embedding: List[float], n_results: int = 5):
        """Perform semantic search using a query embedding."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results
