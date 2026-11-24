"""Flexible magnitude tables.

A "flexible" table is one the user gets to define at query time: pick the
variables to cross and the quantity to total. Cantabular's whole job is to
serve these on demand, which is what makes protecting them hard: the same
businesses appear in many different tables, so the protection has to stay
consistent across all of them.

Here a table is built from microdata by choosing one or more dimensions
(for example industry by region). For every combination of categories we keep:

* the count of businesses in the cell,
* the total turnover (the magnitude),
* the individual contributions, sorted largest first.

We keep the contributions because the disclosure risk rules need to look at
the biggest one or two contributors in each cell, not just the total.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .microdata import Microdata


Key = Tuple[str, ...]


@dataclass
class Cell:
    key: Key
    contributions: List[float]  # sorted descending
    record_keys: List[float] = None  # record keys of the contributors

    def __post_init__(self) -> None:
        if self.record_keys is None:
            self.record_keys = []

    @property
    def count(self) -> int:
        return len(self.contributions)

    @property
    def total(self) -> float:
        return sum(self.contributions)


@dataclass
class Table:
    dims: List[str]
    cells: Dict[Key, Cell]

    def get(self, key: Key) -> Cell:
        return self.cells[key]

    def counts(self) -> Dict[Key, int]:
        return {k: c.count for k, c in self.cells.items()}

    def totals(self) -> Dict[Key, float]:
        return {k: c.total for k, c in self.cells.items()}

    def keys(self) -> List[Key]:
        return list(self.cells.keys())


def _value(business, dim: str) -> str:
    return getattr(business, dim)


def build(md: Microdata, dims: Sequence[str]) -> Table:
    """Build a magnitude table over the given dimensions.

    ``dims`` is a list of Business attribute names, for example
    ``["industry", "region"]``.
    """
    dims = list(dims)
    contrib: Dict[Key, List[float]] = {}
    rkeys: Dict[Key, List[float]] = {}
    for b in md.businesses:
        key: Key = tuple(_value(b, d) for d in dims)
        contrib.setdefault(key, []).append(b.turnover)
        rkeys.setdefault(key, []).append(b.record_key)

    cells: Dict[Key, Cell] = {}
    for key, values in contrib.items():
        values_sorted = sorted(values, reverse=True)
        cells[key] = Cell(
            key=key,
            contributions=values_sorted,
            record_keys=rkeys[key],
        )

    return Table(dims=dims, cells=cells)
