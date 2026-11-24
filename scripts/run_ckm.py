"""Protect a frequency table with the Cell Key Method and measure the cost.

Also checks the property that makes the method worth using: ask for the same
cell in two different tables and you get the same perturbed count.

Usage:
    python scripts/run_ckm.py --dims industry area --seed 1 --max-distortion 2
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cellguard import ckm, microdata, tabulate, utility


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dims", nargs="+", default=["industry", "area"])
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--max-distortion", type=int, default=2)
    ap.add_argument("--out", default="reports/ckm.txt")
    args = ap.parse_args()

    md = microdata.generate(n=args.n, seed=args.seed)
    table = tabulate.build(md, args.dims)
    ptable = ckm.build_ptable(max_distortion=args.max_distortion)

    true_counts, pert_counts = ckm.apply_to_table(table, ptable)
    u = utility.count_utility(true_counts, pert_counts)

    # Consistency check: rebuild the same table with the columns swapped. The
    # cells are the same groups of businesses, so the perturbed counts must
    # match cell for cell.
    table2 = tabulate.build(md, list(reversed(args.dims)))
    _, pert2 = ckm.apply_to_table(table2, ptable)
    mismatches = 0
    for key, cell in table.cells.items():
        swapped = tuple(reversed(key))
        if pert_counts[key] != pert2[swapped]:
            mismatches += 1

    lines = []
    lines.append(f"table: {' x '.join(args.dims)}  cells={len(table.cells)}")
    lines.append(f"ptable: max_distortion={ptable.max_distortion} "
                 f"mean_abs_bias={ptable.mean_abs_bias():.4f}")
    lines.append("utility: " + u.summary())
    lines.append(f"consistency check across re-ordered table: "
                 f"{mismatches} mismatches out of {len(table.cells)} cells")
    text = "\n".join(lines)
    print(text)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
