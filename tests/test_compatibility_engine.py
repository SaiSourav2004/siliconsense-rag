import pytest
from src.schemas import RequirementSpec, ComponentSpec, Evidence
from src.compatibility import CompatibilityEngine

def create_evidence(field, value):
    return Evidence(field=field, value=value, source="test.pdf", page=1, chunk_id="c1", confidence=1.0, evidence_text="")

def test_voltage_pass():
    engine = CompatibilityEngine()
    req = RequirementSpec(voltage_min=3.0, voltage_max=3.6)
    comp = ComponentSpec(voltage_min=create_evidence("v", 1.8), voltage_max=create_evidence("v", 3.6))
    res = engine.evaluate(req, comp)
    assert res.constraint_results[0].status == "PASS"

def test_voltage_fail():
    engine = CompatibilityEngine()
    req = RequirementSpec(voltage_min=5.0, voltage_max=5.5)
    comp = ComponentSpec(voltage_min=create_evidence("v", 1.8), voltage_max=create_evidence("v", 3.6))
    res = engine.evaluate(req, comp)
    assert res.constraint_results[0].status == "FAIL"

def test_voltage_unknown():
    engine = CompatibilityEngine()
    req = RequirementSpec(voltage_min=3.0)
    comp = ComponentSpec()
    res = engine.evaluate(req, comp)
    assert res.constraint_results[0].status == "UNKNOWN"

def test_voltage_boundary():
    engine = CompatibilityEngine()
    req = RequirementSpec(voltage_min=3.3, voltage_max=3.3)
    comp = ComponentSpec(voltage_min=create_evidence("v", 1.8), voltage_max=create_evidence("v", 3.3))
    res = engine.evaluate(req, comp)
    assert res.constraint_results[0].status == "PASS"

def test_flash_pass():
    engine = CompatibilityEngine()
    req = RequirementSpec(min_flash_kb=128)
    comp = ComponentSpec(flash_kb=create_evidence("f", 256))
    assert engine.evaluate(req, comp).constraint_results[0].status == "PASS"

def test_flash_fail():
    engine = CompatibilityEngine()
    req = RequirementSpec(min_flash_kb=256)
    comp = ComponentSpec(flash_kb=create_evidence("f", 128))
    assert engine.evaluate(req, comp).constraint_results[0].status == "FAIL"

def test_flash_unknown():
    engine = CompatibilityEngine()
    req = RequirementSpec(min_flash_kb=256)
    assert engine.evaluate(req, ComponentSpec()).constraint_results[0].status == "UNKNOWN"

def test_sram_pass():
    engine = CompatibilityEngine()
    assert engine.evaluate(RequirementSpec(min_sram_kb=32), ComponentSpec(sram_kb=create_evidence("s", 64))).constraint_results[0].status == "PASS"

def test_sram_fail():
    engine = CompatibilityEngine()
    assert engine.evaluate(RequirementSpec(min_sram_kb=64), ComponentSpec(sram_kb=create_evidence("s", 32))).constraint_results[0].status == "FAIL"

def test_sram_unknown():
    engine = CompatibilityEngine()
    assert engine.evaluate(RequirementSpec(min_sram_kb=64), ComponentSpec()).constraint_results[0].status == "UNKNOWN"

def test_gpio_pass():
    engine = CompatibilityEngine()
    assert engine.evaluate(RequirementSpec(min_gpio=20), ComponentSpec(gpio_count=create_evidence("g", 30))).constraint_results[0].status == "PASS"

def test_gpio_fail():
    engine = CompatibilityEngine()
    assert engine.evaluate(RequirementSpec(min_gpio=40), ComponentSpec(gpio_count=create_evidence("g", 30))).constraint_results[0].status == "FAIL"

def test_gpio_unknown():
    engine = CompatibilityEngine()
    assert engine.evaluate(RequirementSpec(min_gpio=20), ComponentSpec()).constraint_results[0].status == "UNKNOWN"

def test_frequency_pass():
    engine = CompatibilityEngine()
    req = RequirementSpec(frequency_min_mhz=100)
    comp = ComponentSpec(frequency_mhz=create_evidence("fq", 120))
    assert engine.evaluate(req, comp).constraint_results[0].status == "PASS"

def test_frequency_fail():
    engine = CompatibilityEngine()
    req = RequirementSpec(frequency_min_mhz=150)
    comp = ComponentSpec(frequency_mhz=create_evidence("fq", 120))
    assert engine.evaluate(req, comp).constraint_results[0].status == "FAIL"

def test_frequency_unknown():
    engine = CompatibilityEngine()
    assert engine.evaluate(RequirementSpec(frequency_min_mhz=100), ComponentSpec()).constraint_results[0].status == "UNKNOWN"

def test_interfaces_pass():
    engine = CompatibilityEngine()
    req = RequirementSpec(interfaces=["SPI", "I2C"])
    comp = ComponentSpec(interfaces=[create_evidence("i", "SPI"), create_evidence("i", "I2C"), create_evidence("i", "UART")])
    assert engine.evaluate(req, comp).constraint_results[0].status == "PASS"

def test_interfaces_fail():
    engine = CompatibilityEngine()
    req = RequirementSpec(interfaces=["CAN"])
    comp = ComponentSpec(interfaces=[create_evidence("i", "SPI")])
    assert engine.evaluate(req, comp).constraint_results[0].status == "FAIL"

def test_interfaces_unknown():
    engine = CompatibilityEngine()
    assert engine.evaluate(RequirementSpec(interfaces=["SPI"]), ComponentSpec()).constraint_results[0].status == "UNKNOWN"

def test_package_pass():
    engine = CompatibilityEngine()
    req = RequirementSpec(package="LQFP64")
    comp = ComponentSpec(packages=[create_evidence("p", "LQFP-64")])
    assert engine.evaluate(req, comp).constraint_results[0].status == "PASS"

def test_package_fail():
    engine = CompatibilityEngine()
    req = RequirementSpec(package="BGA100")
    comp = ComponentSpec(packages=[create_evidence("p", "LQFP-64")])
    assert engine.evaluate(req, comp).constraint_results[0].status == "FAIL"

def test_package_unknown():
    engine = CompatibilityEngine()
    assert engine.evaluate(RequirementSpec(package="LQFP64"), ComponentSpec()).constraint_results[0].status == "UNKNOWN"

def test_all_pass():
    engine = CompatibilityEngine()
    req = RequirementSpec(voltage_min=3.0, min_flash_kb=128)
    comp = ComponentSpec(voltage_min=create_evidence("v", 1.8), voltage_max=create_evidence("v", 3.3), flash_kb=create_evidence("f", 256))
    res = engine.evaluate(req, comp)
    assert res.overall_status == "POTENTIAL_MATCH"

def test_one_fail():
    engine = CompatibilityEngine()
    req = RequirementSpec(voltage_min=3.0, min_flash_kb=512)
    comp = ComponentSpec(voltage_min=create_evidence("v", 1.8), voltage_max=create_evidence("v", 3.3), flash_kb=create_evidence("f", 256))
    res = engine.evaluate(req, comp)
    assert res.overall_status == "INCOMPATIBLE"

def test_multiple_fail():
    engine = CompatibilityEngine()
    req = RequirementSpec(min_flash_kb=512, min_sram_kb=128)
    comp = ComponentSpec(flash_kb=create_evidence("f", 256), sram_kb=create_evidence("s", 32))
    assert engine.evaluate(req, comp).overall_status == "INCOMPATIBLE"

def test_one_unknown():
    engine = CompatibilityEngine()
    req = RequirementSpec(min_flash_kb=128, min_sram_kb=128)
    comp = ComponentSpec(flash_kb=create_evidence("f", 256))
    assert engine.evaluate(req, comp).overall_status == "INSUFFICIENT_EVIDENCE"

def test_fail_plus_unknown():
    engine = CompatibilityEngine()
    req = RequirementSpec(min_flash_kb=512, min_sram_kb=128)
    comp = ComponentSpec(flash_kb=create_evidence("f", 256)) # FAIL on flash, UNKNOWN on sram
    assert engine.evaluate(req, comp).overall_status == "INCOMPATIBLE" # FAIL > UNKNOWN

def test_empty_specification():
    engine = CompatibilityEngine()
    assert engine.evaluate(RequirementSpec(), ComponentSpec()).overall_status == "POTENTIAL_MATCH"

def test_deterministic_repeated_result():
    engine = CompatibilityEngine()
    req = RequirementSpec(min_flash_kb=128)
    comp = ComponentSpec(flash_kb=create_evidence("f", 256))
    res1 = engine.evaluate(req, comp)
    res2 = engine.evaluate(req, comp)
    assert res1.model_dump() == res2.model_dump()

def test_no_fabrication():
    engine = CompatibilityEngine()
    req = RequirementSpec(min_flash_kb=128)
    comp = ComponentSpec()
    res = engine.evaluate(req, comp)
    assert res.overall_status == "INSUFFICIENT_EVIDENCE"
    assert res.constraint_results[0].actual_value == "UNKNOWN"
