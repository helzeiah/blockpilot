"""Verify the cleaning pipeline against the paper's published counts.

Chen et al. describe three cleaning steps but not their parameters. Step 3's
connectivity was determined empirically: their total of 1,547,699 steps across
2,500 houses is only reachable with 26-connectivity.

    connectivity          kept    removed   vs paper
    6-conn           1,483,203    122,417    -64,496
    18-conn          1,546,070     59,550     -1,629
    26-conn          1,548,170     57,450       +471

Face-only adjacency splits structures joined through terrain, which never
appears in the placement log, so it over-fragments.

No excavation threshold is applied. Every break/place ratio cutoff tested
undershoots the paper's count, so whatever they used removed very little. The
~5 house residual is unresolved. See decisions/002.

Usage:
    python research/verify_cleaning.py
"""

from __future__ import annotations

import argparse
import time
from itertools import pairwise
from pathlib import Path

from blockpilot.data import iter_clean_houses, l1

PAPER_HOUSES = 2_500
PAPER_STEPS = 1_547_699
PAPER_EQ1 = 67.9
PAPER_LE5 = 93.7


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=Path("data/houses"))
    args = parser.parse_args()

    started = time.perf_counter()
    n_houses = n_pos = n_pairs = n_eq1 = n_le5 = 0
    for _house_id, placements in iter_clean_houses(args.data):
        n_houses += 1
        n_pos += len(placements)
        for (a, _), (b, _) in pairwise(placements):
            distance = l1(a, b)
            n_pairs += 1
            if distance == 1:
                n_eq1 += 1
            if distance <= 5:
                n_le5 += 1
    elapsed = time.perf_counter() - started

    eq1 = 100 * n_eq1 / n_pairs
    le5 = 100 * n_le5 / n_pairs
    print(f"\n{'':<14}{'ours':>13}{'paper':>13}{'diff':>11}")
    print("-" * 51)
    print(f"{'houses':<14}{n_houses:>13,}{PAPER_HOUSES:>13,}{n_houses-PAPER_HOUSES:>+11,}")
    print(f"{'placements':<14}{n_pos:>13,}{PAPER_STEPS:>13,}{n_pos-PAPER_STEPS:>+11,}")
    print(f"{'L1 == 1':<14}{eq1:>12.1f}%{PAPER_EQ1:>12.1f}%{eq1-PAPER_EQ1:>+10.1f}%")
    print(f"{'L1 <= 5':<14}{le5:>12.1f}%{PAPER_LE5:>12.1f}%{le5-PAPER_LE5:>+10.1f}%")
    print("-" * 51)
    print(f"{n_pairs:,} pairs in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
