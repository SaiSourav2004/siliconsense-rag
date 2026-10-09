import pytest
from src.schemas import RequirementSpec, ComponentSpec, CompatibilityResult, ConstraintResult
from src.ranking import RankingEngine

@pytest.fixture
def engine():
    return RankingEngine()

def create_mock_candidate(part_number, status, constraints):
    c_res = CompatibilityResult(
        part_number=part_number,
        overall_status=status,
        constraint_results=constraints,
        summary="",
        evidence=[]
    )
    c_spec = ComponentSpec(part_number=part_number)
    return (c_spec, c_res)

def test_fully_compatible(engine):
    req = RequirementSpec()
    c1 = create_mock_candidate("A", "POTENTIAL_MATCH", [ConstraintResult(constraint="flash_kb", required_value=128, actual_value=256, status="PASS", reason="")])
    ranked = engine.rank_candidates(req, [c1])
    assert ranked[0].part_number == "A"
    assert ranked[0].compatibility_status == "POTENTIAL_MATCH"

def test_strong_beats_weak(engine):
    req = RequirementSpec()
    c_strong = create_mock_candidate("Strong", "POTENTIAL_MATCH", [ConstraintResult(constraint="flash_kb", required_value=128, actual_value=512, status="PASS", reason="")])
    c_weak = create_mock_candidate("Weak", "POTENTIAL_MATCH", [ConstraintResult(constraint="flash_kb", required_value=128, actual_value=128, status="PASS", reason="")])
    ranked = engine.rank_candidates(req, [c_weak, c_strong])
    assert ranked[0].part_number == "Strong"
    assert ranked[1].part_number == "Weak"
    assert ranked[0].score > ranked[1].score

def test_hard_gate(engine):
    req = RequirementSpec()
    c_inc = create_mock_candidate("B", "INCOMPATIBLE", [
        ConstraintResult(constraint="flash_kb", required_value=128, actual_value=1024, status="PASS", reason=""),
        ConstraintResult(constraint="package", required_value="LQFP", actual_value="BGA", status="FAIL", reason="")
    ])
    c_match = create_mock_candidate("A", "POTENTIAL_MATCH", [
        ConstraintResult(constraint="flash_kb", required_value=128, actual_value=128, status="PASS", reason=""),
        ConstraintResult(constraint="package", required_value="LQFP", actual_value="LQFP", status="PASS", reason="")
    ])
    ranked = engine.rank_candidates(req, [c_inc, c_match])
    assert ranked[0].part_number == "A"
    assert ranked[1].part_number == "B"

def test_insufficient_evidence(engine):
    req = RequirementSpec()
    c_ins = create_mock_candidate("C", "INSUFFICIENT_EVIDENCE", [ConstraintResult(constraint="flash_kb", required_value=128, actual_value="UNKNOWN", status="UNKNOWN", reason="")])
    c_match = create_mock_candidate("A", "POTENTIAL_MATCH", [ConstraintResult(constraint="flash_kb", required_value=128, actual_value=256, status="PASS", reason="")])
    ranked = engine.rank_candidates(req, [c_ins, c_match])
    assert ranked[0].part_number == "A"
    assert ranked[1].part_number == "C"

def test_empty_candidates(engine):
    ranked = engine.rank_candidates(RequirementSpec(), [])
    assert len(ranked) == 0

def test_tie_breaking(engine):
    req = RequirementSpec()
    c1 = create_mock_candidate("B", "POTENTIAL_MATCH", [ConstraintResult(constraint="flash_kb", required_value=128, actual_value=128, status="PASS", reason="")])
    c2 = create_mock_candidate("A", "POTENTIAL_MATCH", [ConstraintResult(constraint="flash_kb", required_value=128, actual_value=128, status="PASS", reason="")])
    ranked = engine.rank_candidates(req, [c1, c2])
    assert ranked[0].part_number == "A"
    assert ranked[1].part_number == "B"

def test_score_range(engine):
    req = RequirementSpec()
    c1 = create_mock_candidate("A", "POTENTIAL_MATCH", [ConstraintResult(constraint="flash_kb", required_value=128, actual_value=128000, status="PASS", reason="")])
    ranked = engine.rank_candidates(req, [c1])
    assert ranked[0].score is not None
    assert 0 <= ranked[0].score <= 100

def test_reasons(engine):
    req = RequirementSpec()
    c1 = create_mock_candidate("A", "POTENTIAL_MATCH", [ConstraintResult(constraint="flash_kb", required_value=128, actual_value=256, status="PASS", reason="")])
    ranked = engine.rank_candidates(req, [c1])
    assert any("Fully compatible" in r for r in ranked[0].ranking_reasons)
    
def test_unknown_remains_unknown(engine):
    req = RequirementSpec()
    c1 = create_mock_candidate("C", "INSUFFICIENT_EVIDENCE", [ConstraintResult(constraint="flash_kb", required_value=128, actual_value="UNKNOWN", status="UNKNOWN", reason="")])
    ranked = engine.rank_candidates(req, [c1])
    assert "flash_kb" in ranked[0].uncertainty_fields
    
def test_incompatible_has_no_score(engine):
    req = RequirementSpec()
    c1 = create_mock_candidate("D", "INCOMPATIBLE", [ConstraintResult(constraint="flash_kb", required_value=128, actual_value=64, status="FAIL", reason="")])
    ranked = engine.rank_candidates(req, [c1])
    assert ranked[0].score is None
    assert ranked[0].score_breakdown == {}
