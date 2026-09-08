"""Tests for the scoring pipeline -- no network, offline scorer only."""
import os
import sys

sys.path.insert(0, "src")
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import qualify
from enrich import enrich, load_icp
from models import LeadScore, tier_for

ICP = load_icp()


def _lead(**kw):
    base = {"lead_id": "L1", "company": "ACME", "industry": "SaaS",
            "employees": 300, "region": "United States", "annual_revenue_m": 40,
            "source": "Demo request",
            "description": "We're hiring and migrating off our legacy stack."}
    base.update(kw)
    return base


def test_tier_boundaries():
    assert tier_for(80) == "Hot"
    assert tier_for(70) == "Warm"
    assert tier_for(45) == "Nurture"
    assert tier_for(44) == "Disqualify"


def test_good_lead_scores_high():
    score, _ = qualify(_lead(), ICP)
    assert isinstance(score, LeadScore)
    assert score.tier in ("Hot", "Warm")
    assert score.draft_email          # Hot/Warm get an email


def test_enrich_detects_signals():
    e = enrich(_lead(), ICP)
    assert "hiring" in e["signals"] and "migrating" in e["signals"]
    assert e["industry_match"] and e["size_match"] and e["region_match"]


def test_guardrail_disqualifies_blocked_industry():
    score, _ = qualify(_lead(industry="Government"), ICP)
    assert score.tier == "Disqualify"
    assert score.draft_email == ""    # never draft outreach for a disqualified lead


def test_guardrail_disqualifies_blocked_region():
    score, _ = qualify(_lead(region="Sanctioned Region"), ICP)
    assert score.tier == "Disqualify"


def test_schema_rejects_bad_score():
    try:
        LeadScore(lead_id="x", score=150, tier="Hot")   # score > 100
    except Exception:
        return
    raise AssertionError("Pydantic should reject score > 100")


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in list(globals().items())
             if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
            passed += 1
        except Exception:
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"\n{passed}/{len(tests)} passed")
