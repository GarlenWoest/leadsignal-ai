"""Measure the scorer against the ground-truth 'converted' label. Treats
Hot+Warm as 'route it' (positive) and reports precision/recall/F1, a confusion
matrix, and how many real conversions land in the top score decile."""
import numpy as np


def _prf(tp, fp, fn):
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return prec, rec, f1


def evaluate(scored_df):
    """scored_df needs columns: score, tier, converted."""
    df = scored_df
    predicted_pos = df["tier"].isin(["Hot", "Warm"])
    y = df["converted"].astype(bool)

    tp = int((predicted_pos & y).sum())
    fp = int((predicted_pos & ~y).sum())
    fn = int((~predicted_pos & y).sum())
    tn = int((~predicted_pos & ~y).sum())
    prec, rec, f1 = _prf(tp, fp, fn)

    # how many true conversions are in the top 10% by score
    n_top = max(1, int(len(df) * 0.10))
    top = df.nlargest(n_top, "score")
    coverage = top["converted"].mean()

    return {
        "n": len(df),
        "precision": round(prec, 3),
        "recall": round(rec, 3),
        "f1": round(f1, 3),
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "top_decile_conversion_rate": round(float(coverage), 3),
        "base_rate": round(float(y.mean()), 3),
    }


def threshold_sweep(scored_df, steps=19):
    """Precision/recall as the score cutoff moves -- for a PR-style curve."""
    y = scored_df["converted"].astype(bool).to_numpy()
    s = scored_df["score"].to_numpy()
    out = []
    for thr in np.linspace(30, 85, steps):
        pos = s >= thr
        tp = int((pos & y).sum())
        fp = int((pos & ~y).sum())
        fn = int((~pos & y).sum())
        prec, rec, _ = _prf(tp, fp, fn)
        out.append({"threshold": float(thr), "precision": prec, "recall": rec})
    return out
