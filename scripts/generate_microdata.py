"""Generate synthetic business microdata and write it to a CSV.

Usage:
    python scripts/generate_microdata.py --n 4000 --seed 1 --out data/microdata.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cellguard import microdata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="data/microdata.csv")
    args = ap.parse_args()

    md = microdata.generate(n=args.n, seed=args.seed)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bid", "region", "area", "industry", "turnover", "record_key"])
        for b in md.businesses:
            w.writerow(
                [b.bid, b.region, b.area, b.industry, b.turnover, f"{b.record_key:.6f}"]
            )
    print(f"wrote {len(md)} businesses to {args.out}")


if __name__ == "__main__":
    main()
