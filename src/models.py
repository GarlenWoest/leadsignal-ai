"""The structured output every scorer must return. Using Pydantic means a
malformed LLM response fails loudly here instead of leaking downstream."""
from typing import List, Literal

from pydantic import BaseModel, Field

Tier = Literal["Hot", "Warm", "Nurture", "Disqualify"]


class LeadScore(BaseModel):
    lead_id: str
    score: int = Field(ge=0, le=100)
    tier: Tier
    fit_reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    recommended_action: str = ""
    draft_email: str = ""
    scored_by: str = "offline"          # "llm" or "offline"


def tier_for(score: int) -> Tier:
    if score >= 80:
        return "Hot"
    if score >= 70:
        return "Warm"
    if score >= 45:
        return "Nurture"
    return "Disqualify"
