import pytest
from unittest.mock import MagicMock, patch
from src.schemas import RequirementSpec, CompatibilityResult, CandidateRanking, ConstraintResult
from src.explainer import GeminiExplainer

def test_missing_evidence_ui_handling():
    """
    Test how the UI components would handle missing evidence.
    This simulates the data that would be passed to Streamlit.
    """
    # Create a result with missing evidence
    res = CompatibilityResult(
        part_number="STM32F103",
        overall_status="INSUFFICIENT_EVIDENCE",
        constraint_results=[
            ConstraintResult(
                constraint="flash_kb", 
                required_value=128, 
                actual_value="UNKNOWN", 
                status="UNKNOWN", 
                reason="Missing Flash memory evidence", 
                evidence=None
            )
        ],
        summary="One or more required constraints lack evidence."
    )
    
    assert res.overall_status == "INSUFFICIENT_EVIDENCE"
    assert res.constraint_results[0].status == "UNKNOWN"
    assert res.constraint_results[0].evidence is None

def test_gemini_explainer_fallback():
    """
    Test that the GeminiExplainer provides a safe fallback without making a real API call
    when the API key is not available.
    """
    req = RequirementSpec(part_number="STM32F103", min_flash_kb=128)
    res = CompatibilityResult(
        part_number="STM32F103",
        overall_status="INCOMPATIBLE",
        constraint_results=[
            ConstraintResult(
                constraint="flash_kb", required_value=128, actual_value=64, 
                status="FAIL", reason="Component flash is 64 KB"
            )
        ],
        summary="One or more hard constraints failed."
    )
    rank = CandidateRanking(
        part_number="STM32F103",
        compatibility_status="INCOMPATIBLE",
        score=None
    )
    
    # Instantiate without API key by patching os.environ
    with patch.dict('os.environ', {}, clear=True):
        explainer = GeminiExplainer()
        explanation = explainer.explain(req, res, rank)
        
        # Ensure it generated a fallback
        assert "Fallback explanation used" in explanation.limitations
        assert "INCOMPATIBLE" in explanation.summary
        assert "flash_kb" in explanation.summary

def test_ui_labeling_logic():
    """
    Simulate the UI labeling logic for Target Part vs Alternative Candidate
    """
    req_part_number = "STM32F103C8"
    
    # 1. Target part
    rank_part_number = "STM32F103C8"
    is_target = req_part_number and rank_part_number.upper() == req_part_number.upper()
    label = "🎯 [Target Part]" if is_target else "🔄 [Alternative Candidate]" if req_part_number else ""
    assert label == "🎯 [Target Part]"
    
    # 2. Alternative part
    rank_part_number_alt = "STM32F401RE"
    is_target_alt = req_part_number and rank_part_number_alt.upper() == req_part_number.upper()
    label_alt = "🎯 [Target Part]" if is_target_alt else "🔄 [Alternative Candidate]" if req_part_number else ""
    assert label_alt == "🔄 [Alternative Candidate]"
    
    # 3. No target specified
    req_part_number_none = None
    is_target_none = req_part_number_none and rank_part_number.upper() == req_part_number_none.upper()
    label_none = "🎯 [Target Part]" if is_target_none else "🔄 [Alternative Candidate]" if req_part_number_none else ""
    assert label_none == ""
