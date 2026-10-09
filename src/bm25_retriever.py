import os
import json
import pickle
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any

class BM25Retriever:
    def __init__(self, persist_dir: str = "data/processed"):
        self.persist_dir = persist_dir
        self.index_path = os.path.join(self.persist_dir, "bm25_index.pkl")
        self.corpus_path = os.path.join(self.persist_dir, "bm25_corpus.json")
        self.bm25 = None
        self.corpus_metadata = []
        
    def _tokenize(self, text: str) -> List[str]:
        # Simple whitespace tokenization and lowercase.
        # Can be improved with regex for alphanumeric if needed.
        return text.lower().split()

    def build_or_load(self, chunks: List[Dict[str, Any]] = None):
        """
        Builds the BM25 index from chunks if not exists, otherwise loads from disk.
        """
        if os.path.exists(self.index_path) and os.path.exists(self.corpus_path):
            # Load
            with open(self.index_path, "rb") as f:
                self.bm25 = pickle.load(f)
            with open(self.corpus_path, "r", encoding="utf-8") as f:
                self.corpus_metadata = json.load(f)
        else:
            # Build
            if not chunks:
                raise ValueError("BM25 index not found and no chunks provided to build it.")
                
            tokenized_corpus = []
            for c in chunks:
                tokenized_corpus.append(self._tokenize(c["text"]))
                self.corpus_metadata.append({
                    "chunk_id": c["chunk_id"],
                    "source": c["source"],
                    "page": c["page"],
                    "text": c["text"]
                })
                
            self.bm25 = BM25Okapi(tokenized_corpus)
            
            # Persist
            with open(self.index_path, "wb") as f:
                pickle.dump(self.bm25, f)
            with open(self.corpus_path, "w", encoding="utf-8") as f:
                json.dump(self.corpus_metadata, f)

    def search(self, query: str, top_k: int = 15) -> List[Dict[str, Any]]:
        if not self.bm25:
            raise ValueError("BM25 index not loaded.")
            
        tokenized_query = self._tokenize(query)
        doc_scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_n = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
        
        results = []
        for rank, idx in enumerate(top_n, start=1):
            score = doc_scores[idx]
            if score > 0:
                meta = self.corpus_metadata[idx]
                results.append({
                    "chunk_id": meta["chunk_id"],
                    "source": meta["source"],
                    "page": meta["page"],
                    "text": meta["text"],
                    "bm25_score": score,
                    "bm25_rank": rank
                })
                
        return results
