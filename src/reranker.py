from flashrank import Ranker, RerankRequest
from typing import List, Dict, Any

class FlashRankReranker:
    def __init__(self, model_name: str = "ms-marco-MiniLM-L-12-v2", cache_dir: str = "data/models"):
        # The Ranker initializes the model automatically.
        self.ranker = Ranker(model_name=model_name, cache_dir=cache_dir)
        
    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not candidates:
            return []
            
        # FlashRank expects passages as a list of dicts with 'id' and 'text'
        passages = []
        for c in candidates:
            passages.append({
                "id": c["chunk_id"],
                "text": c["text"]
            })
            
        rerank_request = RerankRequest(query=query, passages=passages)
        results = self.ranker.rerank(rerank_request)
        
        # results are returned ordered by score.
        # we need to map back the metadata from the candidates list to the reranked list.
        candidate_map = {c["chunk_id"]: c for c in candidates}
        
        final_results = []
        for rank, res in enumerate(results[:top_k], start=1):
            chunk_id = res["id"]
            meta = candidate_map[chunk_id].copy()
            meta["rerank_score"] = res["score"]
            meta["rerank_rank"] = rank
            final_results.append(meta)
            
        return final_results
