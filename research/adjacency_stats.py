"""Placement-locality statistics for 3D-Craft, used to validate the loader.

Targets from Chen et al. (ICCV 2019), Figure 2a: 67.9% of blocks are placed 1
step (L1) from the previously placed block, 93.7% within 5. The paper does not
define "previously placed block", so three candidate definitions are computed
and compared against the published figures.

Result, 2026-09-15, all 2,517 houses, before the component filter:

    definition                 L1 == 1   L1 <= 5         pairs   houses
    all_actions                  60.9%     95.6%     2,814,025    2,517
    placements_only              66.2%     94.4%     1,981,400    2,515
    surviving_placements         67.7%     93.6%     1,603,105    2,513
    target (paper)               67.9%     93.7%             -        -

The three definitions increase monotonically toward the target as cleaning is
applied. Adding the component filter closes the rest; see
research/verify_cleaning.py.

Usage:
    python research/adjacency_stats.py
"""

from __future__ import annotations

import argparse
from itertools import pairwise
from pathlib import Path

from blockpilot.data import (
    DEFINITIONS,
    iter_house_paths,
    l1,
    load_actions,
    placements_for_definition,
)

TARGET_EQ1 = 67.9
TARGET_LE5 = 93.7


def adjacency_stats(root: Path, definition: str) -> dict[str, float | int]:
    """Pool the locality statistic over every house under `root`.

    Pairs are formed within a house only. Averaging is micro: one global pair
    counter, so large houses carry proportionally more weight.
    """
    n_eq1 = n_le5 = n_pairs = n_houses = 0
    for house in iter_house_paths(root):
        placements = placements_for_definition(load_actions(house), definition)
        positions = [pos for pos, _ in placements]

        house_pairs = 0
        for prev, curr in pairwise(positions):
            distance = l1(prev, curr)
            house_pairs += 1
            if distance == 1:
                n_eq1 += 1
            if distance <= 5:
                n_le5 += 1

        if house_pairs:
            n_houses += 1
            n_pairs += house_pairs

    return {
        "pct_eq1": 100.0 * n_eq1 / n_pairs if n_pairs else 0.0,
        "pct_le5": 100.0 * n_le5 / n_pairs if n_pairs else 0.0,
        "n_pairs": n_pairs,
        "n_houses": n_houses,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=Path("data/houses"))
    parser.add_argument("--definitions", nargs="+", choices=DEFINITIONS,
                        default=list(DEFINITIONS))
    args = parser.parse_args()

    print(f"\n{'definition':<24}{'L1 == 1':>10}{'L1 <= 5':>10}{'pairs':>14}{'houses':>9}")
    print("-" * 67)
    for name in args.definitions:
        r = adjacency_stats(args.data, name)
        print(f"{name:<24}{r['pct_eq1']:>9.1f}%{r['pct_le5']:>9.1f}%"
              f"{r['n_pairs']:>14,}{r['n_houses']:>9,}")
    print("-" * 67)
    print(f"{'target (paper)':<24}{TARGET_EQ1:>9.1f}%{TARGET_LE5:>9.1f}%{'-':>14}{'-':>9}")


if __name__ == "__main__":
    main()
