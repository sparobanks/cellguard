"""Draw the risk-utility map for the Cell Key Method.

For a range of maximum-distortion settings we measure:

* utility cost: the mean absolute change to a cell count,
* small-cell exposure: the share of genuinely small cells (true count 1 or 2)
  that are still published at their exact true value, where an attacker could
  trust them.

Stronger settings push exposure down but cost more utility. Plotting one
against the other is the confidentiality map that disclosure control teams use
to choose an operating point.

Usage:
    python scripts/make_ru_plot.py --seed 1 --out reports/risk_utility.png
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cellguard import ckm, microdata, tabulate, utility


def small_cell_exposure(true_counts, pert_counts) -> float:
    small = [k for k, v in true_counts.items() if v in (1, 2)]
    if not small:
        return 0.0
    exposed = sum(1 for k in small if pert_counts[k] == true_counts[k])
    return exposed / len(small)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="reports/risk_utility.png")
    args = ap.parse_args()

    md = microdata.generate(n=args.n, seed=args.seed)
    table = tabulate.build(md, ["industry", "area"])

    distortions = [1, 2, 3, 4, 5, 6]
    xs, ys = [], []
    for D in distortions:
        ptable = ckm.build_ptable(max_distortion=D)
        true_counts, pert_counts = ckm.apply_to_table(table, ptable)
        u = utility.count_utility(true_counts, pert_counts)
        xs.append(u.mean_abs_error)
        ys.append(small_cell_exposure(true_counts, pert_counts) * 100)

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.plot(xs, ys, "-o", color="#2b6cb0", linewidth=2, markersize=7, zorder=3)
    for D, x, y in zip(distortions, xs, ys):
        ax.annotate(f"D={D}", (x, y), textcoords="offset points",
                    xytext=(8, 6), fontsize=9, color="#2d3748")
    ax.set_xlabel("Utility cost  (mean absolute change to a count)")
    ax.set_ylabel("Small-cell exposure  (% of true 1s and 2s left exact)")
    ax.set_title("Cell Key Method: risk versus utility")
    ax.grid(True, color="#e2e8f0", zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"wrote {args.out}")
    for D, x, y in zip(distortions, xs, ys):
        print(f"  D={D}: utility_cost={x:.3f}  exposure={y:.1f}%")


if __name__ == "__main__":
    main()
