"""Score one enriched lead into a LeadScore.

If ANTHROPIC_API_KEY is set we ask Claude (structured JSON, validated by Pydantic).
Otherwise we fall back to a transparent rule-based scorer so the pipeline still
runs offline -- the eval and demo use this fallback, which is called out in the
README. Set the key to score with the model.
"""
import json
import os

from models import LeadScore, tier_for

MODEL = os.environ.get("LEADSIGNAL_MODEL", "claude-sonnet-5")
PROMPT_PATH = "prompts/score_lead.md"


# ---------- offline rule-based scorer ----------------------------------------
def _offline_score(e, icp):
    w = icp["weights"]
    intent = min(e["signal_count"] / 3.0, 1.0)
    fit = (w["industry"] * e["industry_match"]
           + w["size"] * e["size_match"]
           + w["region"] * e["region_match"]
           + w["intent"] * intent)
    score = int(round(fit * 100))

    reasons, risks = [], []
    reasons.append(f"Industry {e['industry']} " +
                   ("matches ICP" if e["industry_match"] else "is outside ICP"))
    (reasons if e["size_match"] else risks).append(
        f"{e['employees']:,} employees " +
        ("in target range" if e["size_match"] else "outside target size"))
    (reasons if e["region_match"] else risks).append(
        f"{e['region']} " + ("is a target region" if e["region_match"]
                             else "is outside target regions"))
    if e["signals"]:
        reasons.append("Intent signals: " + ", ".join(e["signals"]))
    else:
        risks.append("No intent signals in the inbound message")

    tier = tier_for(score)
    action = {"Hot": "Route to AE for same-day outreach",
              "Warm": "AE outreach within 48h",
              "Nurture": "Add to nurture sequence",
              "Disqualify": "Do not route"}[tier]
    return LeadScore(lead_id=e["lead_id"], score=score, tier=tier,
                     fit_reasons=reasons, risks=risks,
                     recommended_action=action,
                     draft_email=_draft_email(e, tier), scored_by="offline")


HOOKS = {
    "hiring": "saw you're hiring across the team",
    "raised": "congrats on the recent raise",
    "series": "congrats on the recent round",
    "migrating": "saw you're migrating off legacy tooling",
    "scaling": "saw you're scaling into new markets",
    "compliance": "saw compliance is on your roadmap",
    "integration": "saw you're after tighter CRM integration",
    "replacing": "saw you're evaluating a vendor switch",
    "new office": "saw you're opening a new office",
    "expanding": "saw you're expanding",
    "modernizing": "saw you're modernizing the stack",
}


def _draft_email(e, tier):
    if tier in ("Nurture", "Disqualify"):
        return ""
    hook = HOOKS.get(e["signals"][0], "came across your team") if e["signals"] \
        else "came across your team"
    return (f"Hi there — {hook}. Teams like yours in {e['industry']} use us to "
            f"cut manual reporting time. Worth a quick 15 minutes this week?")


# ---------- Claude scorer ----------------------------------------------------
def _llm_score(e, icp):
    import anthropic  # imported lazily so offline mode needs no SDK network

    prompt = open(PROMPT_PATH).read()
    payload = {k: e[k] for k in ["lead_id", "company", "industry", "employees",
                                 "region", "annual_revenue_m", "source",
                                 "description", "signals"]}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL, max_tokens=700,
        system=prompt.replace("{{ICP}}", json.dumps(icp)),
        messages=[{"role": "user",
                   "content": f"Score this lead. Return ONLY JSON.\n{json.dumps(payload)}"}],
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1].lstrip("json").strip()
    data = json.loads(text)
    data["lead_id"] = e["lead_id"]
    data["scored_by"] = "llm"
    return LeadScore.model_validate(data)


def score_lead(enriched, icp):
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return _llm_score(enriched, icp)
        except Exception as exc:      # never let one bad response kill a batch
            print(f"[llm] fell back to offline for {enriched['lead_id']}: {exc}")
    return _offline_score(enriched, icp)
