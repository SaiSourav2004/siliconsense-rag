import os
import json
from typing import Optional
from pydantic import ValidationError
from google import genai
from google.genai import types

from src.schemas import RequirementSpec, CompatibilityResult, CandidateRanking, ExplanationResponse
from src.evidence import EvidenceFormatter
from langsmith import traceable

class GeminiExplainer:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    @traceable(run_type="llm", name="generate_explanation")
    def explain(self, req: RequirementSpec, res: CompatibilityResult, rank: CandidateRanking) -> ExplanationResponse:
        trace = EvidenceFormatter.generate_decision_trace(res)
        
        prompt = f"""
You are an expert hardware engineering assistant. Your job is to explain the computed compatibility and ranking of a candidate component against user requirements.
You MUST rely STRICTLY on the provided constraints and evidence trace. DO NOT invent citations, specifications, or alter the compatibility status.

Candidate Part: {rank.part_number}
Computed Compatibility Status: {rank.compatibility_status}
Computed Preference Score: {rank.score}
Ranking Reasons: {rank.ranking_reasons}

Evidence Trace:
{trace}

Generate a structured response explaining:
- summary: A short text summarizing why the candidate received its compatibility status and score.
- evidence_backed_claims: A list of claims explicitly supported by the evidence trace (include source/page in the claim).
- uncertainties: Any UNKNOWN constraints or lack of evidence.
- conflicts: Any conflicting data.
- limitations: Acknowledge what the system couldn't verify.
- verification_disclaimer: A disclaimer that this is preliminary engineering screening and not a guaranteed drop-in replacement.
"""

        if not self.client:
            return self._generate_fallback(res, rank)

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExplanationResponse,
                    temperature=0.0
                ),
            )
            
            # The SDK will automatically parse the structured output as JSON text
            parsed_data = json.loads(response.text)
            
            # Additional integrity check: Ensure model did not contradict hard constraints
            summary_lower = parsed_data.get("summary", "").lower()
            
            if res.overall_status == "INCOMPATIBLE":
                # If it claims compatibility despite the hard fail, reject it.
                contradictions = ["is compatible", "fully compatible", "perfect match", "meets all requirements", "suitable for"]
                if any(c in summary_lower for c in contradictions) and "not" not in summary_lower and "incompatible" not in summary_lower:
                    return self._generate_fallback(res, rank)

            # Prepend the authoritative status to guarantee the LLM cannot hide it.
            authoritative_prefix = f"STATUS: {res.overall_status}. "
            if not parsed_data.get("summary", "").startswith(authoritative_prefix):
                parsed_data["summary"] = authoritative_prefix + parsed_data.get("summary", "")

            return ExplanationResponse(**parsed_data)

        except Exception as e:
            # Fallback on any API failure, rate limit, JSON error, or validation error
            return self._generate_fallback(res, rank)

    def _generate_fallback(self, res: CompatibilityResult, rank: CandidateRanking) -> ExplanationResponse:
        fails = [c.constraint for c in res.constraint_results if c.status == "FAIL"]
        unknowns = [c.constraint for c in res.constraint_results if c.status == "UNKNOWN"]
        passes = [c.constraint for c in res.constraint_results if c.status == "PASS"]
        
        summary = f"The candidate {res.part_number} is {res.overall_status}. "
        if fails: summary += f"It failed on: {', '.join(fails)}. "
        if unknowns: summary += f"It lacked evidence for: {', '.join(unknowns)}."
        
        claims = [f"{c.constraint} is satisfied based on retrieved evidence." for c in res.constraint_results if c.status == "PASS"]
        
        return ExplanationResponse(
            summary=summary,
            evidence_backed_claims=claims,
            uncertainties=[f"Missing evidence for {u}" for u in unknowns],
            conflicts=[],
            limitations="Fallback explanation used (API unavailable or failed).",
            verification_disclaimer="This is a preliminary engineering screening based on automated extraction. Manual verification of the datasheet is strictly required."
        )
