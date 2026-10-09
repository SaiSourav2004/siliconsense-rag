from typing import List, Tuple, Optional
from src.schemas import RequirementSpec, ComponentSpec, CompatibilityResult, CandidateRanking
from langsmith import traceable

class RankingEngine:
    """
    Deterministic candidate ranking engine.
    Applies a strict hard compatibility gate (POTENTIAL_MATCH > INSUFFICIENT_EVIDENCE > INCOMPATIBLE)
    and then ranks via a soft scoring model. INCOMPATIBLE candidates are assigned no score.
    """
    
    @traceable(run_type="chain", name="rank_candidates")
    def rank_candidates(self, req: RequirementSpec, candidates: List[Tuple[ComponentSpec, CompatibilityResult]]) -> List[CandidateRanking]:
        ranked = []
        for comp, res in candidates:
            total_constraints = len(res.constraint_results)
            known_constraints = sum(1 for c in res.constraint_results if c.status != "UNKNOWN")
            
            completeness = known_constraints / total_constraints if total_constraints > 0 else 1.0
            uncertainties = [c.constraint for c in res.constraint_results if c.status == "UNKNOWN"]
            
            score: Optional[float] = 0.0
            breakdown = {}
            reasons = []
            
            if res.overall_status == "INCOMPATIBLE":
                # Do not assign preference score to incompatible candidates
                score = None
                fails = [c.constraint for c in res.constraint_results if c.status == "FAIL"]
                reasons.append(f"Hard constraints failed: {', '.join(fails)}")
                if uncertainties:
                    reasons.append(f"Missing evidence for: {', '.join(uncertainties)}")
            else:
                # Score base 0-50 for evidence completeness
                completeness_score = completeness * 50.0
                score += completeness_score
                breakdown['completeness'] = completeness_score
                
                if completeness < 1.0:
                    reasons.append(f"Missing evidence for: {', '.join(uncertainties)}")
                    reasons.append("Score is provisional due to missing constraints.")
                    
                # Score base 0-50 for positive margins on numeric constraints
                margin_score = 0.0
                for c in res.constraint_results:
                    if c.status == "PASS" and c.constraint in ["flash_kb", "sram_kb", "gpio_count", "frequency_mhz"]:
                        try:
                            req_val = float(c.required_value)
                            act_val = float(c.actual_value)
                            if req_val > 0:
                                margin = min(1.0, (act_val - req_val) / req_val)
                            else:
                                margin = 1.0
                            margin_score += margin * 15.0 # up to 15 points per numeric match
                        except (ValueError, TypeError):
                            pass
                            
                margin_score = min(50.0, margin_score)
                score += margin_score
                breakdown['margins'] = margin_score
                
                if margin_score > 0:
                    reasons.append("Exceeds minimum numerical requirements.")
                    
                if res.overall_status == "POTENTIAL_MATCH":
                    reasons.append("Fully compatible with all requirements.")

            part_num = res.part_number if res.part_number else "Unknown Part"
            
            cr = CandidateRanking(
                part_number=part_num,
                compatibility_status=res.overall_status,
                score=round(score, 2) if score is not None else None,
                score_breakdown=breakdown,
                ranking_reasons=reasons,
                evidence_completeness=round(completeness, 2),
                uncertainty_fields=uncertainties
            )
            ranked.append(cr)
            
        tier_map = {
            "POTENTIAL_MATCH": 3,
            "INSUFFICIENT_EVIDENCE": 2,
            "INCOMPATIBLE": 1
        }
        
        # Tie-breaking rules:
        # 1. Tier (Desc)
        # 2. Score (Desc, None -> -1.0)
        # 3. Completeness (Desc)
        # 4. Part number (Asc - stable secondary tiebreaker)
        ranked.sort(key=lambda x: x.part_number)
        ranked.sort(key=lambda x: (
            tier_map.get(x.compatibility_status, 0),
            x.score if x.score is not None else -1.0,
            x.evidence_completeness
        ), reverse=True)
        
        for i, r in enumerate(ranked, 1):
            r.rank = i
            
        return ranked
