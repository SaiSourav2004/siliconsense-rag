import pytest
from src.schemas import RequirementSpec, CompatibilityResult, CandidateRanking, ConstraintResult
from src.explainer import GeminiExplainer

def test_explainer_fallback_mode(monkeypatch):
    # Ensure no API key is present
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    explainer = GeminiExplainer()
    assert explainer.client is None
    
    req = RequirementSpec()
    res = CompatibilityResult(
        part_number="TEST_MCU",
        overall_status="INCOMPATIBLE",
        summary="Failed hard constraints",
        constraint_results=[
            ConstraintResult(constraint="flash_kb", required_value=128, actual_value=64, status="FAIL", reason="")
        ]
    )
    rank = CandidateRanking(
        part_number="TEST_MCU",
        compatibility_status="INCOMPATIBLE",
        score=None,
        ranking_reasons=["Hard constraints failed"]
    )
    
    explanation = explainer.explain(req, res, rank)
    
    # Verify fallback behavior
    assert "TEST_MCU is INCOMPATIBLE" in explanation.summary
    assert "failed on: flash_kb" in explanation.summary
    assert "preliminary engineering screening" in explanation.verification_disclaimer
    assert "Fallback explanation used" in explanation.limitations

def test_explainer_unknowns_fallback(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    explainer = GeminiExplainer()
    
    res = CompatibilityResult(
        part_number="TEST_MCU",
        overall_status="INSUFFICIENT_EVIDENCE",
        summary="Missing",
        constraint_results=[
            ConstraintResult(constraint="flash_kb", required_value=128, actual_value="UNKNOWN", status="UNKNOWN", reason="")
        ]
    )
    rank = CandidateRanking(
        part_number="TEST_MCU",
        compatibility_status="INSUFFICIENT_EVIDENCE",
        score=40.0
    )
    
    explanation = explainer.explain(RequirementSpec(), res, rank)
    assert any("Missing evidence for flash_kb" in u for u in explanation.uncertainties)

def test_explainer_rejects_contradictory_incompatible_claim(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    class FakeMockResponse:
        text = '{"summary": "The candidate is compatible and meets all requirements.", "evidence_backed_claims": [], "uncertainties": [], "conflicts": [], "limitations": "", "verification_disclaimer": ""}'

    class FakeModels:
        def generate_content(self, *args, **kwargs):
            return FakeMockResponse()

    class FakeClient:
        models = FakeModels()

    explainer = GeminiExplainer()
    explainer.client = FakeClient()
    
    res = CompatibilityResult(
        part_number="TEST_MCU",
        overall_status="INCOMPATIBLE",
        summary="Failed hard constraints",
        constraint_results=[
            ConstraintResult(constraint="flash_kb", required_value=128, actual_value=64, status="FAIL", reason="")
        ]
    )
    rank = CandidateRanking(
        part_number="TEST_MCU",
        compatibility_status="INCOMPATIBLE",
        score=None,
        ranking_reasons=["Hard constraints failed"]
    )
    
    explanation = explainer.explain(RequirementSpec(), res, rank)
    
    # Should fallback because it claimed "is compatible" while status is INCOMPATIBLE
    assert "Fallback explanation used" in explanation.limitations
    assert "TEST_MCU is INCOMPATIBLE" in explanation.summary

