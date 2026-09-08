"""Turn a raw lead row into the features the scorer reasons over: does it match
the ICP on industry/size/region, and what intent signals appear in its text."""
import json


def load_icp(path="config/icp.json"):
    return json.load(open(path))


def detected_signals(text, icp):
    t = (text or "").lower()
    return [s for s in icp["intent_signals"] if s.lower() in t]


def enrich(lead, icp):
    emp = int(lead["employees"])
    lo, hi = icp["employee_range"]
    signals = detected_signals(lead.get("description", ""), icp)
    return {
        **lead,
        "industry_match": lead["industry"] in icp["target_industries"],
        "size_match": lo <= emp <= hi,
        "region_match": lead["region"] in icp["target_regions"],
        "signals": signals,
        "signal_count": len(signals),
        "disqualified": (lead["industry"] in icp["disqualifiers"]["industries"]
                         or emp > icp["disqualifiers"]["max_employees"]
                         or lead["region"] in icp["disqualifiers"]["blocked_regions"]),
    }
