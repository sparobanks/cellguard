"""Disclosure risk for magnitude tables.

A magnitude cell is risky when someone can back out a single business's
contribution from the published total. The two standard rules both look at the
largest contributors in a cell:

* Minimum contributors. A cell built from one or two businesses should never
  publish a total, because each business can see the total and subtract its own
  value to learn the other's. We flag any cell with fewer than a threshold of
  contributors.

* (n, k) dominance rule. If the largest ``n`` businesses make up more than
  ``k`` of the total, the cell is dominated by them and is unsafe. Agencies
  often use (1, 0.75) and (2, 0.90) together.

* p% rule. The sharpest attacker is the second largest contributor: it knows
  its own value and the published total, so it can estimate the largest
  contributor to within the sum of everyone else. If that remainder is smaller
  than ``p`` percent of the largest contributor, the estimate is too tight and
  the cell is unsafe. Formally the cell is sensitive when
  ``total - c1 - c2 < (p / 100) * c1``.

None of these rules need the microdata, only the sorted contributions we kept
in each cell, which is how a real system assesses risk at tabulation time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .tabulate import Cell, Key, Table


def min_contributors_unsafe(cell: Cell, threshold: int = 3) -> bool:
    return cell.count < threshold


def dominance_unsafe(cell: Cell, n: int = 2, k: float = 0.90) -> bool:
    if cell.count == 0:
        return False
    top = sum(cell.contributions[:n])
    return top > k * cell.total


def p_percent_unsafe(cell: Cell, p: float = 10.0) -> bool:
    """True if the second largest contributor can estimate the largest to
    within ``p`` percent."""
    if cell.count < 3:
        # With fewer than three contributors the p% rule is not well defined;
        # the minimum-contributors rule already covers these cells.
        return cell.count > 0
    c1 = cell.contributions[0]
    c2 = cell.contributions[1]
    remainder = cell.total - c1 - c2
    return remainder < (p / 100.0) * c1


@dataclass
class RiskReport:
    total_cells: int = 0
    min_contrib: List[Key] = field(default_factory=list)
    dominance: List[Key] = field(default_factory=list)
    p_percent: List[Key] = field(default_factory=list)
    unsafe: List[Key] = field(default_factory=list)  # union of the rules

    @property
    def n_unsafe(self) -> int:
        return len(self.unsafe)

    @property
    def share_unsafe(self) -> float:
        if self.total_cells == 0:
            return 0.0
        return self.n_unsafe / self.total_cells

    def summary(self) -> str:
        return (
            f"cells={self.total_cells} unsafe={self.n_unsafe} "
            f"({self.share_unsafe * 100:.1f}%) "
            f"[min_contrib={len(self.min_contrib)} "
            f"dominance={len(self.dominance)} "
            f"p_percent={len(self.p_percent)}]"
        )


@dataclass
class RiskParams:
    min_contributors: int = 3
    dom_n: int = 2
    dom_k: float = 0.90
    p: float = 10.0


def assess(table: Table, params: RiskParams | None = None) -> RiskReport:
    params = params or RiskParams()
    report = RiskReport(total_cells=len(table.cells))
    unsafe: Dict[Key, bool] = {}
    for key, cell in table.cells.items():
        flagged = False
        if min_contributors_unsafe(cell, params.min_contributors):
            report.min_contrib.append(key)
            flagged = True
        if dominance_unsafe(cell, params.dom_n, params.dom_k):
            report.dominance.append(key)
            flagged = True
        if p_percent_unsafe(cell, params.p):
            report.p_percent.append(key)
            flagged = True
        if flagged:
            unsafe[key] = True
    report.unsafe = list(unsafe.keys())
    return report
