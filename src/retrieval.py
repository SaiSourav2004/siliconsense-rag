from typing import List, Dict, Any
from src.embeddings import EmbeddingService
from src.vectorstore import VectorStore
from src.bm25_retriever import BM25Retriever
from src.hybrid_retriever import HybridRetriever
from src.reranker import FlashRankReranker
from langsmith import traceable

class EndToEndRetriever:
    def __init__(self, persist_dir: str = "data/chroma_db", bm25_dir: str = "data/processed"):
        # Dense Retrieval setup
        self.embed_service = EmbeddingService()
        self.vector_store = VectorStore(persist_dir=persist_dir)
        
        # BM25 Retrieval setup
        self.bm25_retriever = BM25Retriever(persist_dir=bm25_dir)
        self.bm25_retriever.build_or_load()
        
        # Fusion and Reranking setup
        self.hybrid = HybridRetriever()
        self.reranker = FlashRankReranker()
        
    @traceable(run_type="retriever", name="dense_search")
    def _dense_search(self, query: str, top_k: int = 15) -> List[Dict[str, Any]]:
        q_emb = self.embed_service.embed_texts([query])[0]
        v_results = self.vector_store.search(q_emb, n_results=top_k)
        
        dense_results = []
        if v_results and len(v_results['ids'][0]) > 0:
            for i in range(len(v_results['ids'][0])):
                meta = v_results['metadatas'][0][i]
                dense_results.append({
                    "chunk_id": v_results['ids'][0][i],
                    "source": meta["source"],
                    "page": meta["page"],
                    "text": v_results['documents'][0][i],
                    "dense_distance": v_results['distances'][0][i] if 'distances' in v_results and v_results['distances'] else None,
                    "dense_rank": i + 1
                })
        return dense_results
        
    @traceable(run_type="chain", name="end_to_end_search")
    def search(self, query: str, dense_k: int = 15, bm25_k: int = 15, final_k: int = 5) -> List[Dict[str, Any]]:
        if not query.strip():
            return []
            
        # 1. Dense Search
        dense_results = self._dense_search(query, top_k=dense_k)
        
        # 2. BM25 Search
        bm25_results = self.bm25_retriever.search(query, top_k=bm25_k)
        
        # 3. Hybrid Fusion
        fused_candidates = self.hybrid.fuse(dense_results, bm25_results)
        
        # 4. Reranking
        final_results = self.reranker.rerank(query, fused_candidates, top_k=final_k)
        
        return final_results
