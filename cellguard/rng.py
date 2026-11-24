"""A small seeded random number generator.

We wrap Python's standard ``random`` module rather than reach for numpy here,
so the data generation and the Cell Key Method are reproducible with nothing
but the standard library. Every draw comes from one seeded stream, so the same
seed always rebuilds the same microdata and the same record keys.
"""

from __future__ import annotations

import math
import random
from typing import List, Sequence


class Rng:
    def __init__(self, seed: int = 0) -> None:
        self._r = random.Random(seed)

    def random(self) -> float:
        """A float in [0, 1)."""
        return self._r.random()

    def randint(self, lo: int, hi: int) -> int:
        """An integer in [lo, hi)."""
        return self._r.randrange(lo, hi)

    def normal(self, mu: float, sigma: float) -> float:
        return self._r.gauss(mu, sigma)

    def lognormal(self, mu: float, sigma: float) -> float:
        return math.exp(self._r.gauss(mu, sigma))

    def choice_weighted(self, items: Sequence[str], weights: Sequence[float]) -> str:
        total = sum(weights)
        x = self._r.random() * total
        acc = 0.0
        for item, w in zip(items, weights):
            acc += w
            if x <= acc:
                return item
        return items[-1]

    def record_keys(self, n: int) -> List[float]:
        """One record key per record, each a float in [0, 1).

        Record keys are the heart of the Cell Key Method: they are fixed to the
        record, drawn once, and never change. A cell's perturbation is decided
        by the sum of its contributors' record keys, so the same cell always
        gets the same treatment.
        """
        return [self._r.random() for _ in range(n)]
