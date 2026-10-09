import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.schemas import RequirementSpec, ComponentSpec, Evidence
from src.compatibility import CompatibilityEngine

def create_evidence(field, value):
    return Evidence(field=field, value=value, source="test.pdf", page=1, chunk_id="c1", confidence=1.0, evidence_text="")

def run_tests():
    engine = CompatibilityEngine()
    
    req = RequirementSpec(
        voltage_min=3.0,
        voltage_max=3.6,
        min_flash_kb=256,
        min_sram_kb=64,
        min_gpio=20,
        interfaces=["SPI", "I2C"],
        package="LQFP64"
    )

    comp_a = ComponentSpec(
        part_number="Candidate A",
        voltage_min=create_evidence("v", 3.0),
        voltage_max=create_evidence("v", 3.6),
        flash_kb=create_evidence("f", 512),
        sram_kb=create_evidence("s", 128),
        gpio_count=create_evidence("g", 30),
        interfaces=[create_evidence("i", "SPI"), create_evidence("i", "I2C"), create_evidence("i", "UART")],
        packages=[create_evidence("p", "LQFP64")],
        frequency_mhz=create_evidence("fq", 120)
    )

    comp_b = ComponentSpec(
        part_number="Candidate B",
        voltage_min=create_evidence("v", 3.0),
        voltage_max=create_evidence("v", 3.6),
        flash_kb=create_evidence("f", 128),  # Fails here
        sram_kb=create_evidence("s", 128),
        gpio_count=create_evidence("g", 30),
        interfaces=[create_evidence("i", "SPI"), create_evidence("i", "I2C"), create_evidence("i", "UART")],
        packages=[create_evidence("p", "LQFP64")],
        frequency_mhz=create_evidence("fq", 120)
    )

    comp_c = ComponentSpec(
        part_number="Candidate C",
        voltage_min=create_evidence("v", 3.0),
        voltage_max=create_evidence("v", 3.6),
        flash_kb=create_evidence("f", 512),
        # SRAM missing
        gpio_count=create_evidence("g", 30),
        interfaces=[create_evidence("i", "SPI"), create_evidence("i", "I2C"), create_evidence("i", "UART")],
        packages=[create_evidence("p", "LQFP64")],
        frequency_mhz=create_evidence("fq", 120)
    )
    
    print("========================================")
    print("PHASE 8 SMOKE TEST")
    print("========================================")
    
    for comp in [comp_a, comp_b, comp_c]:
        res = engine.evaluate(req, comp)
        print(f"\nEvaluating: {comp.part_number}")
        print(f"Overall Status: {res.overall_status}")
        for c in res.constraint_results:
            print(f"  {c.constraint:<15} Req: {str(c.required_value):<15} Act: {str(c.actual_value):<15} -> {c.status}")

if __name__ == "__main__":
    run_tests()
