from typing import List
from src.schemas import CompatibilityResult, ConstraintResult, CandidateRanking

class EvidenceFormatter:
    """
    Formats CompatibilityResult and CandidateRanking into auditable decision traces.
    """
    
    @staticmethod
    def generate_decision_trace(result: CompatibilityResult) -> str:
        trace = []
        trace.append(f"Candidate: {result.part_number}")
        trace.append(f"Overall Status: {result.overall_status}")
        trace.append(f"Summary: {result.summary}")
        trace.append("-" * 40)
        
        for c in result.constraint_results:
            trace.append(f"Constraint: {c.constraint}")
            trace.append(f"Required: {c.required_value}")
            trace.append(f"Actual: {c.actual_value}")
            trace.append(f"Status: {c.status}")
            trace.append(f"Reason: {c.reason}")
            
            if c.evidence:
                trace.append(f"Evidence Source: {c.evidence.source}")
                trace.append(f"Evidence Page: {c.evidence.page}")
                trace.append(f"Evidence Chunk: {c.evidence.chunk_id}")
                text_preview = c.evidence.evidence_text[:100] + "..." if len(c.evidence.evidence_text) > 100 else c.evidence.evidence_text
                trace.append(f"Evidence Text: {text_preview}")
            elif c.status == "UNKNOWN":
                trace.append("Evidence: Reliable evidence unavailable.")
            else:
                trace.append("Evidence: No citation available.")
                
            trace.append("-" * 40)
            
        return "\n".join(trace)
