import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.schemas import RequirementSpec, ComponentSpec, CompatibilityResult, ConstraintResult
from src.ranking import RankingEngine

def run_tests():
    engine = RankingEngine()
    req = RequirementSpec()
    
    # Candidate A: POTENTIAL_MATCH, strong margins
    c_a_res = CompatibilityResult(
        part_number="Candidate A", overall_status="POTENTIAL_MATCH",
        constraint_results=[
            ConstraintResult(constraint="flash_kb", required_value=256, actual_value=1024, status="PASS", reason=""),
            ConstraintResult(constraint="sram_kb", required_value=64, actual_value=256, status="PASS", reason=""),
        ],
        summary=""
    )
    c_a_spec = ComponentSpec(part_number="Candidate A")

    # Candidate B: POTENTIAL_MATCH, weaker margins
    c_b_res = CompatibilityResult(
        part_number="Candidate B", overall_status="POTENTIAL_MATCH",
        constraint_results=[
            ConstraintResult(constraint="flash_kb", required_value=256, actual_value=256, status="PASS", reason=""),
            ConstraintResult(constraint="sram_kb", required_value=64, actual_value=64, status="PASS", reason=""),
        ],
        summary=""
    )
    c_b_spec = ComponentSpec(part_number="Candidate B")

    # Candidate C: INSUFFICIENT_EVIDENCE
    c_c_res = CompatibilityResult(
        part_number="Candidate C", overall_status="INSUFFICIENT_EVIDENCE",
        constraint_results=[
            ConstraintResult(constraint="flash_kb", required_value=256, actual_value=512, status="PASS", reason=""),
            ConstraintResult(constraint="sram_kb", required_value=64, actual_value="UNKNOWN", status="UNKNOWN", reason=""),
        ],
        summary=""
    )
    c_c_spec = ComponentSpec(part_number="Candidate C")
    
    # Candidate D: INCOMPATIBLE
    c_d_res = CompatibilityResult(
        part_number="Candidate D", overall_status="INCOMPATIBLE",
        constraint_results=[
            ConstraintResult(constraint="flash_kb", required_value=256, actual_value=128, status="FAIL", reason=""),
            ConstraintResult(constraint="sram_kb", required_value=64, actual_value=128, status="PASS", reason=""),
        ],
        summary=""
    )
    c_d_spec = ComponentSpec(part_number="Candidate D")

    candidates = [
        (c_b_spec, c_b_res),
        (c_d_spec, c_d_res),
        (c_a_spec, c_a_res),
        (c_c_spec, c_c_res)
    ]
    
    ranked = engine.rank_candidates(req, candidates)
    
    print("--------------------------------")
    print("PHASE 9 RANKING")
    print("--------------------------------")
    print(f"{'Rank':<5} | {'Candidate':<15} | {'Compatibility':<22} | {'Score':<6} | Reasons")
    for r in ranked:
        reasons_str = "; ".join(r.ranking_reasons)
        score_str = str(r.score) if r.score is not None else "None"
        print(f"{r.rank:<5} | {r.part_number:<15} | {r.compatibility_status:<22} | {score_str:<6} | {reasons_str}")

if __name__ == "__main__":
    run_tests()
