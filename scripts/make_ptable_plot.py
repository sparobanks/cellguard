"""Show what the perturbation table does to a few counts.

Each panel is the distribution of the published count for one true count. The
noise is centred on the truth, bounded by the maximum distortion, and never
produces a negative count. A true zero stays zero with certainty, so empty
cells are never invented.

Usage:
    python scripts/make_ptable_plot.py --max-distortion 2 --out reports/ptable.png
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cellguard import ckm


def row_distribution(row):
    """Recover (perturbation -> probability) from the cumulative steps."""
    dist = {}
    prev = 0.0
    for upper, v in row.steps:
        dist[v] = max(0.0, upper - prev)
        prev = upper
    return dist


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-distortion", type=int, default=2)
    ap.add_argument("--out", default="reports/ptable.png")
    args = ap.parse_args()

    ptable = ckm.build_ptable(max_distortion=args.max_distortion)
    counts = [0, 1, 2, 5]

    fig, axes = plt.subplots(1, len(counts), figsize=(11.5, 3.2), sharey=True)
    for ax, c in zip(axes, counts):
        row = ptable.row_for(c)
        dist = row_distribution(row)
        published = sorted(c + v for v in dist)
        probs = [dist[p - c] for p in published]
        ax.bar(published, probs, color="#2b6cb0", width=0.6, zorder=3)
        ax.set_title(f"true count = {c}\nmean shift {row.mean:+.3f}", fontsize=10)
        ax.set_xlabel("published count")
        ax.grid(True, axis="y", color="#e2e8f0", zorder=0)
        ax.set_axisbelow(True)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
    axes[0].set_ylabel("probability")
    fig.suptitle(
        f"Perturbation table (max distortion {args.max_distortion}): "
        f"unbiased, bounded, zeros preserved",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
