"""Deterministic guardrails applied AFTER scoring. Hard disqualifiers (blocked
industry/region, too large) override whatever the model said -- so a confident
but wrong LLM can't route a lead it shouldn't. This is what makes the output
safe to trust in a real workflow."""
from models import LeadScore


def apply_rules(score: LeadScore, enriched) -> LeadScore:
    if enriched["disqualified"]:
        reason = "Hard disqualifier: blocked industry/region or above size cap"
        return score.model_copy(update={
            "tier": "Disqualify",
            "score": min(score.score, 20),
            "risks": list(dict.fromkeys(score.risks + [reason])),
            "recommended_action": "Do not route (guardrail)",
            "draft_email": "",
        })
    return score
