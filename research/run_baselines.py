"""Reproduce the paper's non-learned baseline numbers on our test split.

Reports both denominators. See blockpilot/metrics.py for why.

Usage:
    python research/run_baselines.py
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from blockpilot.baselines import NaiveInertia
from blockpilot.data import load_split
from blockpilot.metrics import DEFAULT_KS, evaluate

PAPER = {"Naive Inertia": {1: 38.7, 5: 47.0, 10: 48.3}}
BASELINES = [("Naive Inertia", NaiveInertia)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=Path("data/houses"))
    parser.add_argument("--split", type=Path, default=Path("splits/houses.json"))
    parser.add_argument("--on", default="test", choices=("train", "val", "test"))
    args = parser.parse_args()

    house_ids = load_split(args.split, args.on)

    for name, factory in BASELINES:
        started = time.perf_counter()
        r = evaluate(factory(), args.data, house_ids, DEFAULT_KS)
        elapsed = time.perf_counter() - started
        paper = PAPER.get(name, {})

        print(f"\n{name}  --  {args.on} split, {r.n_houses} houses, {elapsed:.1f}s")
        print(f"{'':<26}{'acc@1':>9}{'acc@5':>9}{'acc@10':>9}{'steps':>12}")
        print("-" * 65)
        if paper:
            print(f"{'paper':<26}" + "".join(f"{paper[k]:>8.1f}%" for k in DEFAULT_KS)
                  + f"{'313,265':>12}")
        print(f"{'ours, in-window':<26}"
              + "".join(f"{r.accuracy(k, True):>8.1f}%" for k in DEFAULT_KS)
              + f"{r.n_steps_in_window:>12,}")
        print(f"{'ours, all steps':<26}"
              + "".join(f"{r.accuracy(k):>8.1f}%" for k in DEFAULT_KS)
              + f"{r.n_steps:>12,}")
        print("-" * 65)
        print(f"window coverage {r.window_coverage:.1f}% of steps  |  "
              f"abstained {r.n_abstained:,} ({100*r.n_abstained/r.n_steps:.2f}%)")


if __name__ == "__main__":
    main()
