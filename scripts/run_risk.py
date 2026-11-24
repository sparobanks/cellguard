"""Assess disclosure risk on a flexible magnitude table.

Usage:
    python scripts/run_risk.py --dims industry region --seed 1
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cellguard import microdata, risk, tabulate


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dims", nargs="+", default=["industry", "region"])
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--min-contrib", type=int, default=3)
    ap.add_argument("--dom-n", type=int, default=2)
    ap.add_argument("--dom-k", type=float, default=0.90)
    ap.add_argument("--p", type=float, default=10.0)
    ap.add_argument("--out", default="reports/risk.txt")
    args = ap.parse_args()

    md = microdata.generate(n=args.n, seed=args.seed)
    table = tabulate.build(md, args.dims)
    params = risk.RiskParams(
        min_contributors=args.min_contrib,
        dom_n=args.dom_n,
        dom_k=args.dom_k,
        p=args.p,
    )
    report = risk.assess(table, params)

    lines = []
    lines.append(f"table: {' x '.join(args.dims)}")
    lines.append(f"rule: min_contrib<{args.min_contrib}, "
                 f"({args.dom_n},{args.dom_k:.2f}) dominance, p={args.p:.0f}%")
    lines.append(report.summary())
    lines.append("")
    lines.append("sample of unsafe cells (key -> count, total, top share):")
    for key in report.unsafe[:12]:
        cell = table.get(key)
        top_share = (cell.contributions[0] / cell.total) if cell.total else 0.0
        lines.append(
            f"  {key}: count={cell.count} total={cell.total:,.0f} "
            f"top={top_share * 100:.0f}%"
        )
    text = "\n".join(lines)
    print(text)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
