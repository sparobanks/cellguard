"""The Cell Key Method for frequency tables.

This is the method Cantabular uses to protect counts, and it is the part of
this project that mirrors production practice most closely.

The idea in three steps:

1. Every record is given a record key when it enters the data: a random number
   in [0, 1) that is fixed to the record forever.

2. A cell's cell key is the fractional part of the sum of its contributors'
   record keys. It is a number in [0, 1) that depends only on which records are
   in the cell, so the same cell always has the same cell key, in every table.

3. A perturbation table says, for each true count, how much noise to add as a
   function of the cell key. Reading the cell key off the perturbation table
   gives the published count.

Because the cell key is fixed to the records, the noise is fixed to the cell.
Ask for the same cell in a hundred different tables and you get the same
answer every time, so an attacker cannot average the noise away or learn a
protected cell by subtracting two almost-identical tables. That consistency is
the whole point, and it is what a simple "add fresh random noise" approach
fails to give.

The perturbation table below is a readable, honestly simplified version of a
real one. A production table is built by constrained optimisation to hit an
exact noise variance and maximum distortion. Ours is built from a truncated
triangular distribution, then balanced to zero mean wherever the count allows
it, so published totals are not pushed up or down on average. The design
targets are the ones that matter: zeros stay zero, counts never go negative,
no count moves by more than the maximum distortion, and the noise is unbiased.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass
class PRow:
    """One row of the perturbation table: the distribution of the perturbation
    v for a given true count, stored as cumulative thresholds on the cell key.
    """

    count: int
    # (upper cell-key threshold, perturbation v); sorted by threshold ascending
    steps: List[Tuple[float, int]]
    mean: float  # achieved expected perturbation (should be ~0)

    def apply(self, cell_key: float) -> int:
        for upper, v in self.steps:
            if cell_key < upper:
                return v
        return self.steps[-1][1]


@dataclass
class Ptable:
    max_distortion: int
    rows: Dict[int, PRow]
    threshold: int  # counts at or below this are treated as small/at-risk

    def row_for(self, count: int) -> PRow:
        if count in self.rows:
            return self.rows[count]
        # Large counts share the top row's shape.
        top = max(self.rows)
        return self.rows[top]

    def mean_abs_bias(self) -> float:
        return sum(abs(r.mean) for r in self.rows.values()) / len(self.rows)


def _triangular_weights(count: int, D: int) -> Dict[int, float]:
    """Unnormalised symmetric triangular weights over v, truncated so that
    count + v is never negative, and with zero forced to stay zero."""
    if count == 0:
        return {0: 1.0}
    weights: Dict[int, float] = {}
    v_min = max(-D, -count)
    for v in range(v_min, D + 1):
        weights[v] = float(D + 1 - abs(v))
    return weights


def _normalise(weights: Dict[int, float]) -> Dict[int, float]:
    total = sum(weights.values())
    return {v: w / total for v, w in weights.items()}


def _mean(dist: Dict[int, float]) -> float:
    return sum(v * p for v, p in dist.items())


def _balance_mean(dist: Dict[int, float]) -> Dict[int, float]:
    """Nudge probability between the -1 and +1 cells to drive the mean to zero.

    Truncating the triangular distribution at small counts leaves a positive
    mean (we removed some negative perturbations). Moving probability from +1
    toward -1 cancels that bias exactly, as long as both cells exist.
    """
    m = _mean(dist)
    if abs(m) < 1e-12:
        return dist
    if 1 not in dist or -1 not in dist:
        return dist  # cannot balance; caller reports residual bias
    out = dict(dist)
    # Moving mass t from v=+1 to v=-1 changes the mean by -2t. Solve -2t = -m.
    t = m / 2.0
    t = max(-out[-1], min(out[1], t))  # keep both probabilities valid
    out[1] -= t
    out[-1] += t
    return out


def build_ptable(max_distortion: int = 2, max_count: int = 60, threshold: int = 2) -> Ptable:
    rows: Dict[int, PRow] = {}
    for count in range(0, max_count + 1):
        dist = _normalise(_triangular_weights(count, max_distortion))
        dist = _balance_mean(dist)
        # Build cumulative steps on the cell key.
        steps: List[Tuple[float, int]] = []
        acc = 0.0
        for v in sorted(dist):
            acc += dist[v]
            steps.append((acc, v))
        # Guard against floating point: force the last threshold to 1.0.
        steps[-1] = (1.0, steps[-1][1])
        rows[count] = PRow(count=count, steps=steps, mean=_mean(dist))
    return Ptable(max_distortion=max_distortion, rows=rows, threshold=threshold)


def cell_key(record_keys: Sequence[float]) -> float:
    """The fractional part of the sum of the contributors' record keys."""
    s = math.fsum(record_keys)
    return s - math.floor(s)


def perturb_count(true_count: int, ck: float, ptable: Ptable) -> int:
    row = ptable.row_for(true_count)
    v = row.apply(ck)
    out = true_count + v
    return max(0, out)


def apply_to_table(table, ptable: Ptable):
    """Perturb every cell count in a table with the Cell Key Method.

    Returns two dicts keyed by cell: the true counts and the perturbed counts.
    The cell key for each cell comes from its contributors' record keys, so the
    result is fully determined by the data and the perturbation table.
    """
    true_counts = {}
    pert_counts = {}
    for key, cell in table.cells.items():
        ck = cell_key(cell.record_keys)
        true_counts[key] = cell.count
        pert_counts[key] = perturb_count(cell.count, ck, ptable)
    return true_counts, pert_counts

