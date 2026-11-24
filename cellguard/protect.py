"""Protecting magnitude tables.

Counts are protected by the Cell Key Method (see ``ckm.py``). Magnitude cells,
the totals of a continuous quantity, are harder, because a dominated cell leaks
information no matter how you jitter the published number. The long-standing
answer is cell suppression: hide the unsafe cells, then hide a few more so the
hidden ones cannot be recovered by subtracting from the row and column totals.

This module provides two things:

* ``suppress`` for a two-dimensional magnitude table: primary suppression of the
  cells a risk assessment flags, then a secondary suppression pass so that every
  row and every column that has any suppression has at least two suppressed
  cells. With only one hole in a line, the attacker just subtracts the other
  published cells from the line total and recovers it; a second hole closes that.

* ``consistent_perturb`` a key-driven perturbation of magnitude totals, included
  so the two families of method can be compared. It reuses the cell key, so the
  same cell is always perturbed the same way, but we are honest in the README
  that perturbation alone does not protect a dominated cell: suppression or a
  more involved method is still needed there.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from .ckm import cell_key
from .risk import RiskReport
from .tabulate import Key, Table


@dataclass
class MarginTable:
    """A two-dimensional magnitude table with row, column and grand totals."""

    rows: List[str]
    cols: List[str]
    values: Dict[Tuple[str, str], float]  # (row, col) -> total
    counts: Dict[Tuple[str, str], int]

    def row_total(self, r: str) -> float:
        return sum(self.values.get((r, c), 0.0) for c in self.cols)

    def col_total(self, c: str) -> float:
        return sum(self.values.get((r, c), 0.0) for r in self.rows)

    def grand_total(self) -> float:
        return sum(self.values.values())


def to_margin_table(table: Table) -> MarginTable:
    if len(table.dims) != 2:
        raise ValueError("margin table needs a two-dimensional table")
    rows = sorted({k[0] for k in table.keys()})
    cols = sorted({k[1] for k in table.keys()})
    values: Dict[Tuple[str, str], float] = {}
    counts: Dict[Tuple[str, str], int] = {}
    for key, cell in table.cells.items():
        values[(key[0], key[1])] = cell.total
        counts[(key[0], key[1])] = cell.count
    return MarginTable(rows=rows, cols=cols, values=values, counts=counts)


@dataclass
class SuppressionResult:
    primary: Set[Tuple[str, str]] = field(default_factory=set)
    secondary: Set[Tuple[str, str]] = field(default_factory=set)

    @property
    def suppressed(self) -> Set[Tuple[str, str]]:
        return self.primary | self.secondary

    def summary(self) -> str:
        return (
            f"primary={len(self.primary)} secondary={len(self.secondary)} "
            f"total_suppressed={len(self.suppressed)}"
        )


def _lines_needing_cover(
    mt: MarginTable, suppressed: Set[Tuple[str, str]]
) -> List[Tuple[str, str]]:
    """Return ('row', r) or ('col', c) for every line with exactly one
    suppressed cell, which is therefore recoverable from its total."""
    need: List[Tuple[str, str]] = []
    for r in mt.rows:
        s = [c for c in mt.cols if (r, c) in suppressed]
        if len(s) == 1:
            need.append(("row", r))
    for c in mt.cols:
        s = [r for r in mt.rows if (r, c) in suppressed]
        if len(s) == 1:
            need.append(("col", c))
    return need


def suppress(table: Table, report: RiskReport) -> Tuple[MarginTable, SuppressionResult]:
    mt = to_margin_table(table)
    result = SuppressionResult()

    for key in report.unsafe:
        if len(key) == 2:
            result.primary.add((key[0], key[1]))

    suppressed = set(result.primary)

    # Secondary pass: give every under-covered line a second suppressed cell.
    # We pick the smallest-value publishable cell to minimise information lost.
    for _ in range(1000):
        need = _lines_needing_cover(mt, suppressed)
        if not need:
            break
        kind, name = need[0]
        if kind == "row":
            candidates = [
                (mt.values.get((name, c), 0.0), (name, c))
                for c in mt.cols
                if (name, c) not in suppressed and (name, c) in mt.values
            ]
        else:
            candidates = [
                (mt.values.get((r, name), 0.0), (r, name))
                for r in mt.rows
                if (r, name) not in suppressed and (r, name) in mt.values
            ]
        if not candidates:
            break
        candidates.sort()
        choice = candidates[0][1]
        result.secondary.add(choice)
        suppressed.add(choice)

    return mt, result


def consistent_perturb(table: Table, rel_noise: float = 0.01) -> Dict[Key, float]:
    """A cell-key driven perturbation of magnitude totals.

    The cell key maps to a factor in [1 - rel_noise, 1 + rel_noise]. The same
    cell always maps to the same factor, so the perturbation is consistent
    across tables. This is a demonstration of the mechanism, not a safe
    stand-alone protection for dominated cells.
    """
    out: Dict[Key, float] = {}
    for key, cell in table.cells.items():
        ck = cell_key(cell.record_keys)
        factor = 1.0 + rel_noise * (2.0 * ck - 1.0)
        out[key] = cell.total * factor
    return out
