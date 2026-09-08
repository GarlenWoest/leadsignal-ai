"""The scoring pipeline for one lead: enrich -> score (LLM or offline) ->
apply guardrails. Returns a validated LeadScore."""
from enrich import enrich
from llm import score_lead
from rules import apply_rules


def qualify(lead, icp):
    e = enrich(lead, icp)
    score = score_lead(e, icp)
    return apply_rules(score, e), e
