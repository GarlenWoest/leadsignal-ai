"""Make a synthetic inbound-lead list with a ground-truth 'converted' label, so
the scorer can be evaluated against something.

The label depends on ICP fit + intent + a hidden 'budget' factor the scorer
never sees + noise -- so a good scorer lands in the 0.7-0.9 range, not a
suspicious 1.0.
"""
import json
import os

import numpy as np
import pandas as pd

RNG = np.random.default_rng(11)
OUT = "data/leads.csv"

TARGET_IND = ["SaaS", "Fintech", "Healthtech", "E-commerce", "Logistics",
              "Cybersecurity", "MarTech"]
OFF_IND = ["Government", "Nonprofit", "Retail", "Manufacturing", "Construction",
           "Education", "Hospitality"]
TARGET_REGION = ["United States", "Canada", "United Kingdom", "Germany", "Netherlands"]
OFF_REGION = ["India", "Brazil", "Australia", "France", "Sanctioned Region"]
SOURCES = ["Demo request", "Webinar", "Content download", "Cold inbound",
           "Referral", "Event scan"]

INTENT_PHRASES = {
    "hiring": "We're hiring across engineering and ops.",
    "raised": "We recently raised a Series B round.",
    "migrating": "We're migrating off our legacy stack.",
    "scaling": "Scaling the team into new markets.",
    "compliance": "Working toward SOC 2 and compliance.",
    "integration": "Looking for a tool that integrates with our CRM.",
    "replacing": "Actively replacing our current vendor.",
    "new office": "Opening a new office next quarter.",
}
FILLER = ["A team focused on product quality.",
          "We value reliable partners.",
          "Our roadmap is busy this year.",
          "Customer experience is a priority."]


def _size_fit(emp):
    return 1.0 if 50 <= emp <= 2000 else (0.4 if emp <= 5000 else 0.1)


def build(n=400):
    rows = []
    for i in range(n):
        on_target_ind = RNG.random() < 0.55
        industry = RNG.choice(TARGET_IND if on_target_ind else OFF_IND)
        on_target_region = RNG.random() < 0.7
        region = RNG.choice(TARGET_REGION if on_target_region else OFF_REGION)
        employees = int(np.clip(RNG.lognormal(6.0, 1.1), 5, 40000))
        revenue_m = round(employees * RNG.uniform(0.15, 0.5), 1)
        source = RNG.choice(SOURCES)

        # intent strength 0..1, and phrases that reflect it
        intent = float(np.clip(RNG.beta(2, 3) + (0.15 if source in
                        ("Demo request", "Referral") else 0), 0, 1))
        n_phrases = int(round(intent * 3))
        keys = list(RNG.choice(list(INTENT_PHRASES), size=min(n_phrases, 3),
                               replace=False)) if n_phrases else []
        desc = " ".join([INTENT_PHRASES[k] for k in keys] +
                        [RNG.choice(FILLER)])

        ind_fit = 1.0 if on_target_ind else 0.15
        region_fit = 1.0 if on_target_region else 0.3
        size_fit = _size_fit(employees)
        hidden_budget = RNG.random()          # scorer never sees this
        noise = RNG.normal(0, 0.12)

        latent = (0.32 * ind_fit + 0.16 * size_fit + 0.12 * region_fit
                  + 0.25 * intent + 0.15 * hidden_budget + noise)
        converted = int(latent > 0.74)        # ~30% convert, like real inbound

        rows.append({
            "lead_id": f"L{i+1:04d}",
            "company": f"{industry[:3].upper()}-{RNG.integers(1000,9999)}",
            "industry": industry,
            "employees": employees,
            "region": region,
            "annual_revenue_m": revenue_m,
            "source": source,
            "description": desc,
            "converted": converted,          # ground truth (hidden from scorer)
        })
    return pd.DataFrame(rows)


def main():
    os.makedirs("data", exist_ok=True)
    df = build()
    df.to_csv(OUT, index=False)
    print(f"[generate_leads] {len(df)} leads -> {OUT}")
    print(f"[generate_leads] converted rate = {df['converted'].mean():.1%}")


if __name__ == "__main__":
    main()
