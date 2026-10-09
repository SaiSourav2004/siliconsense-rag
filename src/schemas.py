from pydantic import BaseModel, Field
from typing import List, Optional, Any

class RequirementSpec(BaseModel):
    """
    Structured natural-language component requirements.
    Missing fields default to None.
    """
    part_number: Optional[str] = None
    voltage_min: Optional[float] = None
    voltage_max: Optional[float] = None
    min_flash_kb: Optional[int] = None
    min_sram_kb: Optional[int] = None
    min_gpio: Optional[int] = None
    package: Optional[str] = None
    interfaces: Optional[List[str]] = Field(default_factory=list)
    frequency_min_mhz: Optional[float] = None
    frequency_max_mhz: Optional[float] = None
    connectivity: Optional[List[str]] = Field(default_factory=list)


class Evidence(BaseModel):
    """
    Provenance tracking for extracted specifications.
    """
    field: str
    value: Any
    source: str
    page: int
    chunk_id: str
    confidence: float
    evidence_text: str


class ComponentSpec(BaseModel):
    """
    Extracted component specifications with strict evidence metadata.
    """
    part_number: Optional[str] = None
    voltage_min: Optional[Evidence] = None
    voltage_max: Optional[Evidence] = None
    flash_kb: Optional[Evidence] = None
    sram_kb: Optional[Evidence] = None
    gpio_count: Optional[Evidence] = None
    packages: Optional[List[Evidence]] = Field(default_factory=list)
    interfaces: Optional[List[Evidence]] = Field(default_factory=list)
    frequency_mhz: Optional[Evidence] = None
    connectivity: Optional[List[Evidence]] = Field(default_factory=list)

class ConstraintResult(BaseModel):
    constraint: str
    required_value: Any
    actual_value: Any
    status: str  # PASS, FAIL, UNKNOWN
    reason: str
    evidence: Optional[Evidence] = None

class CompatibilityResult(BaseModel):
    part_number: Optional[str] = None
    overall_status: str  # POTENTIAL_MATCH, INCOMPATIBLE, INSUFFICIENT_EVIDENCE
    constraint_results: List[ConstraintResult] = Field(default_factory=list)
    summary: str
    evidence: List[Evidence] = Field(default_factory=list)

class CandidateRanking(BaseModel):
    part_number: str
    compatibility_status: str
    rank: int = 0
    score: Optional[float] = None
    score_breakdown: dict = Field(default_factory=dict)
    ranking_reasons: List[str] = Field(default_factory=list)
    evidence_completeness: float = 0.0
    uncertainty_fields: List[str] = Field(default_factory=list)

class ExplanationResponse(BaseModel):
    summary: str
    evidence_backed_claims: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    limitations: str
    verification_disclaimer: str
