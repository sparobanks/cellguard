"""The spatial strand: finer geography means more risk.

The same businesses are tabulated by industry at two geographic levels: the
five regions, and the twenty smaller areas inside them. Splitting the country
into more pieces spreads the same businesses across more cells, so each cell
has fewer contributors and more of them are dominated by one firm. This chart
shows the share of unsafe cells rising as the geography gets finer, which is
exactly why a flexible table builder has to assess risk per query rather than
once.

Usage:
    python scripts/make_spatial.py --seed 1 --out reports/spatial.png
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cellguard import microdata, risk, tabulate


def unsafe_share(md, dims) -> float:
    table = tabulate.build(md, dims)
    report = risk.assess(table)
    return report.share_unsafe * 100


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="reports/spatial.png")
    args = ap.parse_args()

    md = microdata.generate(n=args.n, seed=args.seed)

    levels = [
        ("National\n(industry only)", ["industry"]),
        ("Region\n(industry x region)", ["industry", "region"]),
        ("Area\n(industry x area)", ["industry", "area"]),
    ]
    labels = [lab for lab, _ in levels]
    shares = [unsafe_share(md, dims) for _, dims in levels]

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    bars = ax.bar(labels, shares, color=["#9ae6b4", "#f6ad55", "#fc8181"], zorder=3)
    for b, s in zip(bars, shares):
        ax.annotate(f"{s:.0f}%", (b.get_x() + b.get_width() / 2, s),
                    textcoords="offset points", xytext=(0, 5),
                    ha="center", fontsize=11, color="#2d3748")
    ax.set_ylabel("Unsafe cells (% of cells in the table)")
    ax.set_title("Risk rises as geography gets finer")
    ax.grid(True, axis="y", color="#e2e8f0", zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"wrote {args.out}")
    for lab, s in zip([l.replace(chr(10), ' ') for l in labels], shares):
        print(f"  {lab}: {s:.1f}% unsafe")


if __name__ == "__main__":
    main()
