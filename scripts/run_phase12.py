import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.schemas import RequirementSpec, CompatibilityResult, CandidateRanking, ConstraintResult
from src.explainer import GeminiExplainer

def run_tests():
    # Force fallback mode by removing the API key
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]
        
    explainer = GeminiExplainer()
    
    from src.schemas import ComponentSpec, Evidence
    from src.compatibility import CompatibilityEngine

    # Construct the same realistic RequirementSpec as Phase 10
    req = RequirementSpec(
        part_number="STM32F103C8",
        voltage_min=3.0,
        voltage_max=3.6,
        min_flash_kb=256,
        min_sram_kb=64
    )
    
    # Construct the same ComponentSpec as Phase 10
    comp = ComponentSpec(
        part_number="STM32F103C8",
        voltage_min=Evidence(
            field="voltage_min", value=1.8, source="DS_stm32f103c8.pdf", page=38, 
            chunk_id="DS_stm32f103c8_p038_c005", confidence=0.9, 
            evidence_text="Operating conditions: VDD = 1.8 to 2.5 V."
        ),
        voltage_max=Evidence(
            field="voltage_max", value=2.5, source="DS_stm32f103c8.pdf", page=38, 
            chunk_id="DS_stm32f103c8_p038_c005", confidence=0.9, 
            evidence_text="Operating conditions: VDD = 1.8 to 2.5 V."
        ),
        flash_kb=Evidence(
            field="flash_kb", value=64, source="DS_stm32f103c8.pdf", page=14, 
            chunk_id="DS_stm32f103c8_p014_c001", confidence=0.9, 
            evidence_text="STM32F103C8 memory density: 64 Kbytes of Flash memory."
        ),
        sram_kb=None # Simulate missing SRAM
    )
    
    engine = CompatibilityEngine()
    res = engine.evaluate(req, comp)
    
    rank = CandidateRanking(
        part_number="STM32F103C8",
        compatibility_status=res.overall_status,
        score=0.0 if res.overall_status == "INCOMPATIBLE" else 50.0,
        ranking_reasons=[res.summary]
    )
    
    explanation = explainer.explain(req, res, rank)
    
    print("========================================")
    print("PHASE 12 GEMINI EXPLAINER (MOCK MODE)")
    print("========================================")
    print(f"Summary: {explanation.summary}")
    print("\nEvidence Backed Claims:")
    for c in explanation.evidence_backed_claims:
        print(f" - {c}")
    print("\nUncertainties:")
    for u in explanation.uncertainties:
        print(f" - {u}")
    print("\nLimitations:")
    print(f" - {explanation.limitations}")
    print("\nDisclaimer:")
    print(f" - {explanation.verification_disclaimer}")

if __name__ == "__main__":
    run_tests()
