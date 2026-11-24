"""Protect a two-dimensional magnitude table by cell suppression.

Usage:
    python scripts/run_suppress.py --seed 1 --dom-k 0.90 --p 10
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cellguard import microdata, protect, risk, tabulate, utility


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--dom-k", type=float, default=0.90)
    ap.add_argument("--p", type=float, default=10.0)
    ap.add_argument("--out", default="reports/suppress.txt")
    args = ap.parse_args()

    md = microdata.generate(n=args.n, seed=args.seed)
    table = tabulate.build(md, ["industry", "region"])
    params = risk.RiskParams(dom_k=args.dom_k, p=args.p)
    report = risk.assess(table, params)

    mt, result = protect.suppress(table, report)
    u = utility.suppression_utility(mt, result.suppressed)

    lines = []
    lines.append("table: industry x region")
    lines.append("risk: " + report.summary())
    lines.append("suppression: " + result.summary())
    lines.append("cost: " + u.summary())
    lines.append("")
    lines.append("published table (x = suppressed):")
    header = "industry".ljust(14) + "".join(c.ljust(10) for c in mt.cols)
    lines.append(header)
    for r in mt.rows:
        row = r.ljust(14)
        for c in mt.cols:
            if (r, c) in result.suppressed:
                row += "x".ljust(10)
            else:
                row += f"{mt.values.get((r, c), 0.0):,.0f}".ljust(10)
        lines.append(row)
    text = "\n".join(lines)
    print(text)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
