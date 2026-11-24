"""Synthetic business microdata.

Each row is one business (a "contributor"). A business has a magnitude value
(here, annual turnover in thousands of pounds) and a few classification
variables we can cross-tabulate on: region, area within the region, and
industry.

Turnover in the real world is very skewed: a handful of large firms sit
alongside many small ones. We draw it from a lognormal distribution so that
some cells end up dominated by one or two big contributors. That domination is
exactly what disclosure control has to deal with, so the synthetic data has to
show it.

The data is generated from a seed, so a given seed always produces the same
microdata. No real business data is used anywhere in this project.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .rng import Rng


REGIONS = ["North", "Midlands", "South", "East", "West"]

# A few areas inside each region. The spatial strand of the project uses these
# to show how finer geography raises disclosure risk.
AREAS_PER_REGION = 4

INDUSTRIES = [
    "Agriculture",
    "Manufacturing",
    "Construction",
    "Retail",
    "Transport",
    "Hospitality",
    "Finance",
    "ICT",
]


@dataclass
class Business:
    """One contributor to the statistics."""

    bid: int
    region: str
    area: str
    industry: str
    turnover: float  # thousands of pounds
    record_key: float = 0.0  # fixed random key, used by the Cell Key Method


@dataclass
class Microdata:
    """A collection of businesses plus the category labels used to tabulate."""

    businesses: List[Business] = field(default_factory=list)
    regions: List[str] = field(default_factory=lambda: list(REGIONS))
    areas: List[str] = field(default_factory=list)
    industries: List[str] = field(default_factory=lambda: list(INDUSTRIES))

    def __len__(self) -> int:
        return len(self.businesses)


def area_name(region: str, i: int) -> str:
    return f"{region}-{i + 1}"


def generate(n: int = 4000, seed: int = 1) -> Microdata:
    """Generate ``n`` businesses.

    Industries are not equally likely: Retail and Manufacturing are common,
    Finance and ICT are rarer, which is what makes some industry-by-area cells
    small and therefore risky.
    """
    rng = Rng(seed)

    areas = []
    for region in REGIONS:
        for i in range(AREAS_PER_REGION):
            areas.append(area_name(region, i))

    # Relative frequency of each industry. Rare industries create small cells.
    industry_weights = {
        "Agriculture": 0.08,
        "Manufacturing": 0.16,
        "Construction": 0.12,
        "Retail": 0.22,
        "Transport": 0.10,
        "Hospitality": 0.14,
        "Finance": 0.08,
        "ICT": 0.10,
    }
    industries = list(industry_weights.keys())
    weights = [industry_weights[k] for k in industries]

    # Each industry has its own turnover scale, so dominance patterns differ.
    industry_scale = {
        "Agriculture": 5.0,
        "Manufacturing": 6.2,
        "Construction": 5.6,
        "Retail": 5.4,
        "Transport": 5.5,
        "Hospitality": 5.0,
        "Finance": 6.6,
        "ICT": 6.0,
    }

    businesses: List[Business] = []
    for bid in range(n):
        region = REGIONS[rng.randint(0, len(REGIONS))]
        area = area_name(region, rng.randint(0, AREAS_PER_REGION))
        industry = rng.choice_weighted(industries, weights)
        # Lognormal turnover: exp(normal). sigma large => heavy tail, so some
        # cells end up dominated by one or two big firms.
        mu = industry_scale[industry]
        sigma = 1.3
        turnover = rng.lognormal(mu, sigma)
        businesses.append(
            Business(
                bid=bid,
                region=region,
                area=area,
                industry=industry,
                turnover=round(turnover, 1),
                record_key=rng.random(),
            )
        )

    return Microdata(
        businesses=businesses,
        regions=list(REGIONS),
        areas=areas,
        industries=industries,
    )
