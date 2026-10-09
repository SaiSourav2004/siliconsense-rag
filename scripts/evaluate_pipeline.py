import os
import sys
import json
import math
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.retrieval import EndToEndRetriever
from src.evaluation import Evaluator
from src.spec_extractor import SpecExtractor
from src.requirement_parser import RequirementParser
from src.compatibility import CompatibilityEngine

def run_evaluation():
    eval_file = os.path.join(ROOT_DIR, "data", "evaluation", "eval_queries.json")
    if not os.path.exists(eval_file):
        print(f"Evaluation dataset missing at {eval_file}")
        return

    with open(eval_file, "r") as f:
        queries = json.load(f)

    # Initialize components
    retriever = EndToEndRetriever(
        persist_dir=os.path.join(ROOT_DIR, "data", "chroma_db"),
        bm25_dir=os.path.join(ROOT_DIR, "data", "processed")
    )
    extractor = SpecExtractor()
    req_parser = RequirementParser()
    comp_engine = CompatibilityEngine()

    all_retrieved_sources = []
    all_ground_truths = []
    
    extraction_results = {"total": 0, "correct_flash": 0, "correct_sram": 0, "correct_voltage": 0}
    decision_results = {"total": 0, "correct_status": 0}

    print(f"Evaluating {len(queries)} queries...\n")

    for q in queries:
        query_text = q["query_text"]
        target = q["target_component"]
        gt_sources = q["relevant_sources"]

        # 1. Retrieval
        try:
            results = retriever.search(query_text, dense_k=30, bm25_k=30, final_k=15)
            retrieved_sources = [r["source"] for r in results]
        except Exception as e:
            print(f"Retrieval failed for '{query_text}': {e}")
            retrieved_sources = []
            results = []

        all_retrieved_sources.append(retrieved_sources)
        all_ground_truths.append(gt_sources)

        # 2. Extraction Verification
        try:
            req = req_parser.parse(query_text)
            spec = extractor.extract(results, expected_part_number=target)
            extraction_results["total"] += 1
            
            if "expected_flash" in q:
                if spec.flash_kb and spec.flash_kb.value == q["expected_flash"]:
                    extraction_results["correct_flash"] += 1
            if "expected_sram" in q:
                if spec.sram_kb and spec.sram_kb.value == q["expected_sram"]:
                    extraction_results["correct_sram"] += 1
            if "expected_voltage_min" in q and "expected_voltage_max" in q:
                if spec.voltage_min and spec.voltage_max:
                    if math.isclose(spec.voltage_min.value, q["expected_voltage_min"], abs_tol=0.1) and \
                       math.isclose(spec.voltage_max.value, q["expected_voltage_max"], abs_tol=0.1):
                        extraction_results["correct_voltage"] += 1
                        
            # 3. Compatibility Decision Verification
            if "expected_status_hint" in q:
                decision_results["total"] += 1
                comp_res = comp_engine.evaluate(req, spec)
                if comp_res.overall_status == q["expected_status_hint"]:
                    decision_results["correct_status"] += 1
        except Exception:
            pass

    # Compute Retrieval Metrics
    for k in [1, 3, 5]:
        hit_rate = Evaluator.calculate_hit_rate(all_retrieved_sources, all_ground_truths, k)
        mrr = Evaluator.calculate_mrr(all_retrieved_sources, all_ground_truths, k)
        recall = Evaluator.calculate_recall(all_retrieved_sources, all_ground_truths, k)
        print(f"Top-{k} Metrics:")
        print(f"  Hit Rate@{k}: {hit_rate:.4f}")
        print(f"  MRR@{k}:      {mrr:.4f}")
        print(f"  Recall@{k}:   {recall:.4f}\n")

    print("Extraction Evaluation (Exact Match):")
    tot = extraction_results["total"]
    if tot > 0:
        print(f"  Flash:   {extraction_results['correct_flash']}/{tot}")
        print(f"  SRAM:    {extraction_results['correct_sram']}/{tot}")
        print(f"  Voltage: {extraction_results['correct_voltage']}/{tot}")
    else:
        print("  No extraction queries evaluated.")
        
    print("\nCompatibility Decision Evaluation:")
    tot_dec = decision_results["total"]
    if tot_dec > 0:
        print(f"  Status Accuracy: {decision_results['correct_status']}/{tot_dec} ({(decision_results['correct_status']/tot_dec)*100:.1f}%)")
    else:
        print("  No decision queries evaluated.")
        
if __name__ == "__main__":
    run_evaluation()
