"""Charts for the README: tier breakdown, score distribution, confusion matrix,
and precision/recall vs the score cutoff."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

ASSETS = "assets"
INK = "#1B2430"
SLATE = "#5E6B7A"
INDIGO = "#3D4EAE"
GRID = "#E4E7EC"
TIER_COLOR = {"Hot": "#1F9D6B", "Warm": "#C99A2E",
              "Nurture": "#3E7CB1", "Disqualify": "#9AA3AE"}
TIER_ORDER = ["Hot", "Warm", "Nurture", "Disqualify"]

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130, "font.family": "DejaVu Sans",
    "font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": INK,
    "axes.titlecolor": INK, "text.color": INK, "xtick.color": SLATE,
    "ytick.color": SLATE, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})


def _save(fig, name):
    fig.tight_layout()
    p = f"{ASSETS}/{name}"
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def tier_breakdown(df):
    counts = df["tier"].value_counts().reindex(TIER_ORDER).fillna(0)
    conv = df.groupby("tier")["converted"].mean().reindex(TIER_ORDER).fillna(0)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    bars = ax.bar(TIER_ORDER, counts, color=[TIER_COLOR[t] for t in TIER_ORDER],
                  edgecolor="white")
    for b, t in zip(bars, TIER_ORDER):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 3,
                f"{int(counts[t])}", ha="center", fontsize=10, color=INK)
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() / 2,
                f"{conv[t]:.0%}\nconvert", ha="center", va="center",
                fontsize=9, color="white", fontweight="bold")
    ax.set_title("Leads by tier (label = actual conversion rate)", fontsize=13,
                 fontweight="bold", loc="left")
    ax.set_ylabel("Leads")
    ax.grid(axis="y", color=GRID, lw=0.8)
    return _save(fig, "01_tier_breakdown.png")


def score_distribution(df):
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    for label, sub in df.groupby(df["converted"].map({1: "Converted", 0: "Did not convert"})):
        ax.hist(sub["score"], bins=np.arange(0, 101, 5), alpha=0.6,
                label=label, color=INDIGO if label == "Converted" else SLATE,
                edgecolor="white")
    for cut, name in [(80, "Hot"), (70, "Warm"), (45, "Nurture")]:
        ax.axvline(cut, color=TIER_COLOR[name], ls="--", lw=1.2)
        ax.text(cut + 1, ax.get_ylim()[1] * 0.9, name, color=TIER_COLOR[name],
                fontsize=8.5)
    ax.set_xlabel("Lead score")
    ax.set_ylabel("Leads")
    ax.set_title("Score distribution — converters skew right", fontsize=13,
                 fontweight="bold", loc="left")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", color=GRID, lw=0.8)
    return _save(fig, "02_score_distribution.png")


def confusion(metrics):
    c = metrics["confusion"]
    m = np.array([[c["tp"], c["fn"]], [c["fp"], c["tn"]]])
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    ax.imshow(m, cmap="Blues")
    labels = [["TP", "FN"], ["FP", "TN"]]
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{labels[i][j]}\n{m[i, j]}", ha="center", va="center",
                    fontsize=13, fontweight="bold",
                    color="white" if m[i, j] > m.max() * 0.5 else INK)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Actually\nconverted", "Did not"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["Routed\n(Hot/Warm)", "Not routed"])
    ax.set_title(f"Confusion — P {metrics['precision']:.0%} / "
                 f"R {metrics['recall']:.0%} / F1 {metrics['f1']:.2f}",
                 fontsize=12, fontweight="bold", loc="left")
    return _save(fig, "03_confusion_matrix.png")


def pr_curve(sweep):
    thr = [d["threshold"] for d in sweep]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(thr, [d["precision"] for d in sweep], color=INDIGO, lw=2,
            marker="o", ms=3, label="Precision")
    ax.plot(thr, [d["recall"] for d in sweep], color="#1F9D6B", lw=2,
            marker="o", ms=3, label="Recall")
    ax.axvline(70, color=SLATE, ls="--", lw=1)
    ax.text(70.5, 0.1, "Route cutoff", color=SLATE, fontsize=8.5)
    ax.set_xlabel("Score threshold")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_title("Precision vs recall as the cutoff moves", fontsize=13,
                 fontweight="bold", loc="left")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(color=GRID, lw=0.8)
    return _save(fig, "04_precision_recall.png")
