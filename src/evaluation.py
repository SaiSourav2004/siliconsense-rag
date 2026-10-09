from typing import List, Dict, Any

class Evaluator:
    @staticmethod
    def calculate_hit_rate(results: List[List[str]], ground_truths: List[List[str]], k: int) -> float:
        hits = 0
        for res, gt in zip(results, ground_truths):
            # Checking if ANY ground truth source is in the top-k results
            top_k = res[:k]
            if any(truth in top_k for truth in gt):
                hits += 1
        return hits / len(results) if results else 0.0

    @staticmethod
    def calculate_mrr(results: List[List[str]], ground_truths: List[List[str]], k: int) -> float:
        mrr_sum = 0.0
        for res, gt in zip(results, ground_truths):
            top_k = res[:k]
            for rank, item in enumerate(top_k, 1):
                if item in gt:
                    mrr_sum += 1.0 / rank
                    break
        return mrr_sum / len(results) if results else 0.0

    @staticmethod
    def calculate_recall(results: List[List[str]], ground_truths: List[List[str]], k: int) -> float:
        recall_sum = 0.0
        for res, gt in zip(results, ground_truths):
            top_k = res[:k]
            hits = sum(1 for truth in gt if truth in top_k)
            if len(gt) > 0:
                recall_sum += hits / len(gt)
            else:
                recall_sum += 1.0
        return recall_sum / len(results) if results else 0.0
