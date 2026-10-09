import pytest
from src.schemas import CompatibilityResult, ConstraintResult, Evidence
from src.evidence import EvidenceFormatter

def create_evidence(val, src="doc.pdf", pg=10, chunk="c10", text="Found val"):
    return Evidence(field="test", value=val, source=src, page=pg, chunk_id=chunk, confidence=1.0, evidence_text=text)

def test_evidence_trace_pass():
    res = CompatibilityResult(
        part_number="TEST_MCU",
        overall_status="POTENTIAL_MATCH",
        summary="All good",
        constraint_results=[
            ConstraintResult(
                constraint="flash_kb",
                required_value=128,
                actual_value=256,
                status="PASS",
                reason="256 >= 128",
                evidence=create_evidence(256)
            )
        ]
    )
    trace = EvidenceFormatter.generate_decision_trace(res)
    assert "Candidate: TEST_MCU" in trace
    assert "Status: POTENTIAL_MATCH" in trace
    assert "Constraint: flash_kb" in trace
    assert "Status: PASS" in trace
    assert "Evidence Source: doc.pdf" in trace
    assert "Evidence Page: 10" in trace
    assert "Evidence Chunk: c10" in trace
    assert "Evidence Text: Found val" in trace

def test_evidence_trace_unknown():
    res = CompatibilityResult(
        part_number="TEST_MCU",
        overall_status="INSUFFICIENT_EVIDENCE",
        summary="Missing",
        constraint_results=[
            ConstraintResult(
                constraint="sram_kb",
                required_value=64,
                actual_value="UNKNOWN",
                status="UNKNOWN",
                reason="No SRAM info",
                evidence=None
            )
        ]
    )
    trace = EvidenceFormatter.generate_decision_trace(res)
    assert "Status: UNKNOWN" in trace
    assert "Evidence: Reliable evidence unavailable." in trace

def test_evidence_trace_fail():
    res = CompatibilityResult(
        part_number="TEST_MCU",
        overall_status="INCOMPATIBLE",
        summary="Fails flash",
        constraint_results=[
            ConstraintResult(
                constraint="flash_kb",
                required_value=256,
                actual_value=64,
                status="FAIL",
                reason="64 < 256",
                evidence=create_evidence(64, text="Flash is 64KB")
            )
        ]
    )
    trace = EvidenceFormatter.generate_decision_trace(res)
    assert "Status: FAIL" in trace
    assert "Evidence Text: Flash is 64KB" in trace

def test_evidence_text_truncation():
    long_text = "A" * 150
    res = CompatibilityResult(
        part_number="TEST_MCU",
        overall_status="POTENTIAL_MATCH",
        summary="",
        constraint_results=[
            ConstraintResult(
                constraint="flash_kb", required_value=128, actual_value=256, status="PASS", reason="",
                evidence=create_evidence(256, text=long_text)
            )
        ]
    )
    trace = EvidenceFormatter.generate_decision_trace(res)
    assert "A" * 100 + "..." in trace
    assert "A" * 101 + "..." not in trace
