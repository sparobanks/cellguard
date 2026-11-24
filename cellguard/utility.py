"""Measuring the cost of protection.

Protection is only useful if the published table is still close enough to the
truth to be worth publishing. These functions put a number on that cost so it
can be traded against risk.

For the Cell Key Method we compare true and perturbed counts. The headline
numbers are the mean absolute error (how far a typical cell moves), the share
of cells that changed at all, and the signed bias (whether the method pushes
counts up or down on average, which should be close to zero).

For suppression the cost is what you can no longer see: the share of cells
hidden and the share of the grand total they held.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Set, Tuple

from .protect import MarginTable


@dataclass
class CountUtility:
    n_cells: int
    mean_abs_error: float
    rmse: float
    share_changed: float
    max_abs_error: int
    bias: float  # mean signed error

    def summary(self) -> str:
        return (
            f"MAE={self.mean_abs_error:.3f} RMSE={self.rmse:.3f} "
            f"changed={self.share_changed * 100:.1f}% "
            f"maxdiff={self.max_abs_error} bias={self.bias:+.3f}"
        )


def count_utility(true_counts: Dict, pert_counts: Dict) -> CountUtility:
    keys = list(true_counts.keys())
    n = len(keys)
    abs_errs = []
    sq = []
    signed = []
    changed = 0
    max_abs = 0
    for k in keys:
        d = pert_counts[k] - true_counts[k]
        abs_errs.append(abs(d))
        sq.append(d * d)
        signed.append(d)
        if d != 0:
            changed += 1
        max_abs = max(max_abs, abs(d))
    mae = sum(abs_errs) / n if n else 0.0
    rmse = math.sqrt(sum(sq) / n) if n else 0.0
    bias = sum(signed) / n if n else 0.0
    return CountUtility(
        n_cells=n,
        mean_abs_error=mae,
        rmse=rmse,
        share_changed=changed / n if n else 0.0,
        max_abs_error=max_abs,
        bias=bias,
    )


@dataclass
class SuppressionUtility:
    n_cells: int
    n_suppressed: int
    share_cells_suppressed: float
    share_total_hidden: float

    def summary(self) -> str:
        return (
            f"suppressed {self.n_suppressed}/{self.n_cells} cells "
            f"({self.share_cells_suppressed * 100:.1f}%), "
            f"hiding {self.share_total_hidden * 100:.1f}% of the grand total"
        )


def suppression_utility(
    mt: MarginTable, suppressed: Set[Tuple[str, str]]
) -> SuppressionUtility:
    n_cells = len(mt.values)
    grand = mt.grand_total()
    hidden = sum(mt.values.get(cell, 0.0) for cell in suppressed)
    return SuppressionUtility(
        n_cells=n_cells,
        n_suppressed=len(suppressed),
        share_cells_suppressed=len(suppressed) / n_cells if n_cells else 0.0,
        share_total_hidden=hidden / grand if grand else 0.0,
    )
