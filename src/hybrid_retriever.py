from typing import List, Dict, Any

class HybridRetriever:
    def __init__(self, k_rrf: int = 60):
        self.k_rrf = k_rrf
        
    def fuse(self, dense_results: List[Dict[str, Any]], bm25_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fuses results using Reciprocal Rank Fusion (RRF).
        RRF_score = 1 / (60 + rank)
        """
        fused_scores = {}
        metadata_map = {}
        
        # Process Dense results
        for item in dense_results:
            chunk_id = item["chunk_id"]
            rank = item.get("dense_rank", 1) # Fallback if not provided
            score = 1.0 / (self.k_rrf + rank)
            fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + score
            metadata_map[chunk_id] = {
                "chunk_id": chunk_id,
                "source": item["source"],
                "page": item["page"],
                "text": item["text"],
                "dense_rank": rank,
                "dense_distance": item.get("dense_distance")
            }
            
        # Process BM25 results
        for item in bm25_results:
            chunk_id = item["chunk_id"]
            rank = item.get("bm25_rank", 1)
            score = 1.0 / (self.k_rrf + rank)
            fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + score
            
            if chunk_id not in metadata_map:
                metadata_map[chunk_id] = {
                    "chunk_id": chunk_id,
                    "source": item["source"],
                    "page": item["page"],
                    "text": item["text"],
                }
            metadata_map[chunk_id]["bm25_rank"] = rank
            metadata_map[chunk_id]["bm25_score"] = item.get("bm25_score")
            
        # Compile final list
        fused_list = []
        for chunk_id, total_rrf in fused_scores.items():
            meta = metadata_map[chunk_id]
            meta["rrf_score"] = total_rrf
            fused_list.append(meta)
            
        # Sort descending by RRF score
        fused_list.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused_list
