"""Deterministic decision layer for optional Gemma normalization."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FallbackDecision(BaseModel):
    use_gemma: bool
    reasons: list[str]
    page_complexity: str

    model_config = ConfigDict(extra="forbid")


class FallbackDecisionEngine:
    """Allow Gemma only when deterministic output needs editorial help."""

    def decide(
        self,
        *,
        confidence_score: float,
        warning_count: int,
        uncertainty_count: int,
        unsupported_claim_count: int,
        step_count: int,
        image_count: int,
    ) -> FallbackDecision:
        reasons: list[str] = []
        complexity = "simple"
        if image_count >= 4 or step_count >= 12:
            complexity = "complex"
            reasons.append("complex_multi_step_page")
        elif image_count >= 3 or step_count >= 8:
            complexity = "medium"
        if confidence_score < 0.80:
            reasons.append("low_confidence")
        if warning_count >= 3:
            reasons.append("too_many_warnings")
        if uncertainty_count >= 5:
            reasons.append("too_many_uncertainties")
        if unsupported_claim_count >= 2:
            reasons.append("unsupported_structure")
        return FallbackDecision(
            use_gemma=bool(reasons), reasons=list(dict.fromkeys(reasons)),
            page_complexity=complexity,
        )
