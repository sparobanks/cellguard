"""Unit tests for CellGuard.

Run with:  python -m pytest -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cellguard import ckm, microdata, protect, risk, tabulate, utility
from cellguard.tabulate import Cell


# ----------------------------------------------------------------------------
# Perturbation table
# ----------------------------------------------------------------------------

def test_ptable_rows_are_distributions():
    pt = ckm.build_ptable(max_distortion=2, max_count=30)
    for row in pt.rows.values():
        # cumulative steps end at 1.0
        assert abs(row.steps[-1][0] - 1.0) < 1e-9


def test_zero_count_stays_zero():
    pt = ckm.build_ptable(max_distortion=3)
    # Whatever the cell key, a true zero must publish as zero.
    for ck in [0.0, 0.1, 0.5, 0.9, 0.999]:
        assert ckm.perturb_count(0, ck, pt) == 0


def test_perturbation_is_bounded_and_non_negative():
    D = 2
    pt = ckm.build_ptable(max_distortion=D, max_count=40)
    for true in range(0, 41):
        for i in range(50):
            ck = i / 50.0
            out = ckm.perturb_count(true, ck, pt)
            assert out >= 0
            assert abs(out - true) <= D


def test_ptable_is_close_to_unbiased():
    pt = ckm.build_ptable(max_distortion=2, max_count=40)
    # Counts of 3 or more can be balanced to exactly zero mean.
    for count in range(3, 41):
        assert abs(pt.rows[count].mean) < 1e-9
    # Overall bias across all rows stays tiny.
    assert pt.mean_abs_bias() < 0.05


# ----------------------------------------------------------------------------
# Cell key
# ----------------------------------------------------------------------------

def test_cell_key_in_unit_interval():
    for keys in ([0.1, 0.2, 0.9], [0.99, 0.99, 0.99], []):
        ck = ckm.cell_key(keys)
        assert 0.0 <= ck < 1.0


def test_cell_key_is_deterministic():
    keys = [0.3, 0.7, 0.123, 0.456]
    assert ckm.cell_key(keys) == ckm.cell_key(keys)


# ----------------------------------------------------------------------------
# Consistency: the headline property of the Cell Key Method
# ----------------------------------------------------------------------------

def test_ckm_consistent_across_table_order():
    md = microdata.generate(n=1500, seed=3)
    pt = ckm.build_ptable(max_distortion=2)
    t1 = tabulate.build(md, ["industry", "area"])
    t2 = tabulate.build(md, ["area", "industry"])
    _, p1 = ckm.apply_to_table(t1, pt)
    _, p2 = ckm.apply_to_table(t2, pt)
    for key in t1.cells:
        assert p1[key] == p2[tuple(reversed(key))]


# ----------------------------------------------------------------------------
# Risk rules
# ----------------------------------------------------------------------------

def test_min_contributors_rule():
    cell = Cell(key=("a",), contributions=[100.0, 50.0])
    assert risk.min_contributors_unsafe(cell, threshold=3)
    cell3 = Cell(key=("a",), contributions=[100.0, 50.0, 10.0])
    assert not risk.min_contributors_unsafe(cell3, threshold=3)


def test_dominance_rule():
    # One firm is 95% of the total: dominated.
    cell = Cell(key=("a",), contributions=[950.0, 30.0, 20.0])
    assert risk.dominance_unsafe(cell, n=2, k=0.90)
    # Evenly split: safe.
    cell2 = Cell(key=("a",), contributions=[100.0, 100.0, 100.0, 100.0])
    assert not risk.dominance_unsafe(cell2, n=2, k=0.90)


def test_p_percent_rule():
    # Second largest can pin the largest very tightly: unsafe.
    cell = Cell(key=("a",), contributions=[1000.0, 900.0, 5.0, 5.0])
    assert risk.p_percent_unsafe(cell, p=10.0)
    # Large remainder hides the largest: safe.
    cell2 = Cell(key=("a",), contributions=[100.0, 90.0, 80.0, 70.0, 60.0])
    assert not risk.p_percent_unsafe(cell2, p=10.0)


# ----------------------------------------------------------------------------
# Tabulation
# ----------------------------------------------------------------------------

def test_tabulate_counts_and_totals():
    md = microdata.generate(n=2000, seed=5)
    table = tabulate.build(md, ["region"])
    # Every business lands in exactly one cell.
    assert sum(c.count for c in table.cells.values()) == len(md)
    total = sum(b.turnover for b in md.businesses)
    tab_total = sum(c.total for c in table.cells.values())
    assert abs(total - tab_total) < 1e-6
    # Contributions are sorted largest first.
    for cell in table.cells.values():
        assert cell.contributions == sorted(cell.contributions, reverse=True)


# ----------------------------------------------------------------------------
# Suppression
# ----------------------------------------------------------------------------

def test_no_single_suppression_in_a_line():
    md = microdata.generate(n=4000, seed=1)
    table = tabulate.build(md, ["industry", "region"])
    report = risk.assess(table)
    mt, result = protect.suppress(table, report)
    suppressed = result.suppressed
    # If a line has any suppression it must have at least two, otherwise the
    # hidden cell is recoverable from the line total.
    for r in mt.rows:
        s = [c for c in mt.cols if (r, c) in suppressed]
        assert len(s) != 1, f"row {r} has a single suppressed cell"
    for c in mt.cols:
        s = [r for r in mt.rows if (r, c) in suppressed]
        assert len(s) != 1, f"col {c} has a single suppressed cell"


def test_primary_cells_are_suppressed():
    md = microdata.generate(n=4000, seed=1)
    table = tabulate.build(md, ["industry", "region"])
    report = risk.assess(table)
    _, result = protect.suppress(table, report)
    for key in report.unsafe:
        assert (key[0], key[1]) in result.suppressed


# ----------------------------------------------------------------------------
# Utility
# ----------------------------------------------------------------------------

def test_count_utility_zero_when_unchanged():
    counts = {("a",): 10, ("b",): 3}
    u = utility.count_utility(counts, dict(counts))
    assert u.mean_abs_error == 0.0
    assert u.share_changed == 0.0
    assert u.bias == 0.0
