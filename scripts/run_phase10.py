import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.schemas import RequirementSpec, ComponentSpec, Evidence
from src.compatibility import CompatibilityEngine
from src.evidence import EvidenceFormatter

def run_tests():
    # Construct a realistic RequirementSpec
    req = RequirementSpec(
        part_number="STM32F103C8",
        voltage_min=3.0,
        voltage_max=3.6,
        min_flash_kb=256,
        min_sram_kb=64
    )
    
    # Construct a realistic ComponentSpec with Evidence
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

    print("========================================")
    print("PHASE 10 EVIDENCE & CITATION TRACE")
    print("========================================")
    
    trace = EvidenceFormatter.generate_decision_trace(res)
    print(trace)

if __name__ == "__main__":
    run_tests()
