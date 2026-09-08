"""Score the whole lead list, evaluate against the labels, write the ranked call
sheet, charts, and a metrics file.

    python src/run.py
"""
import json
import os

import pandas as pd

import viz
from agent import qualify
from enrich import load_icp
from evaluate import evaluate, threshold_sweep

LEADS = "data/leads.csv"


def ensure_leads():
    if not os.path.exists(LEADS):
        import generate_leads
        generate_leads.main()


def score_all(icp):
    df = pd.read_csv(LEADS)
    out = []
    for lead in df.to_dict("records"):
        score, _ = qualify(lead, icp)
        row = score.model_dump()
        row["converted"] = lead["converted"]
        row["company"] = lead["company"]
        row["industry"] = lead["industry"]
        out.append(row)
    return pd.DataFrame(out)


def main():
    os.makedirs("examples", exist_ok=True)
    ensure_leads()
    icp = load_icp()

    scored = score_all(icp)
    mode = "Claude" if os.environ.get("ANTHROPIC_API_KEY") else "offline rule-based"

    metrics = evaluate(scored)
    metrics["scored_by"] = scored["scored_by"].iloc[0]
    sweep = threshold_sweep(scored)

    # ranked call sheet: what a rep actually opens
    call_sheet = (scored[scored["tier"].isin(["Hot", "Warm"])]
                  .sort_values("score", ascending=False)
                  [["lead_id", "company", "industry", "score", "tier",
                    "recommended_action", "draft_email"]])
    call_sheet.to_csv("examples/call_sheet.csv", index=False)

    # one fully-worked example lead
    hot = scored[scored["tier"] == "Hot"].sort_values("score", ascending=False)
    if len(hot):
        with open("examples/sample_scored_lead.json", "w") as f:
            json.dump({k: v for k, v in hot.iloc[0].items()
                       if k != "converted"}, f, indent=2, default=str)

    with open("examples/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    viz.tier_breakdown(scored)
    viz.score_distribution(scored)
    viz.confusion(metrics)
    viz.pr_curve(sweep)

    print(f"[run] scored {len(scored)} leads with the {mode} scorer")
    print(f"[run] precision {metrics['precision']:.0%}  recall {metrics['recall']:.0%}  "
          f"F1 {metrics['f1']}  (base rate {metrics['base_rate']:.0%})")
    print(f"[run] top-decile conversion rate {metrics['top_decile_conversion_rate']:.0%}")
    print(f"[run] call sheet: {len(call_sheet)} leads -> examples/call_sheet.csv")
    print("[run] charts -> assets/   metrics -> examples/metrics.json")


if __name__ == "__main__":
    main()
