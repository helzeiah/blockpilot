"""Freeze a train/val/test split of 3D-Craft houses.

The split is by HOUSE, never by step. Two placements from the same build are
highly predictive of each other, so splitting by step would leak the test set
into training and inflate every number.

Ratios follow the paper: 70/10/20. The paper's own split is 1,750 / 250 / 500
houses and 1,074,647 / 159,787 / 313,265 steps; its exact membership was never
published, so ours is a different random draw of the same shape.

The result is written to splits/houses.json and must not be regenerated. A
changed split silently invalidates comparison against every earlier run.

Usage:
    python research/make_split.py --data data/houses --out splits/houses.json
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from blockpilot.data import iter_clean_houses

SEED = 20260925
RATIOS = {"train": 0.70, "val": 0.10, "test": 0.20}

PAPER = {
    "train": (1_750, 1_074_647),
    "val": (250, 159_787),
    "test": (500, 313_265),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=Path("data/houses"))
    parser.add_argument("--out", type=Path, default=Path("splits/houses.json"))
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    sizes = {name: len(pos) for name, pos in iter_clean_houses(args.data)}
    names = sorted(sizes)                       # sorted first, so the shuffle is reproducible
    random.Random(args.seed).shuffle(names)

    n = len(names)
    n_train = round(n * RATIOS["train"])
    n_val = round(n * RATIOS["val"])
    split = {
        "train": sorted(names[:n_train]),
        "val": sorted(names[n_train : n_train + n_val]),
        "test": sorted(names[n_train + n_val :]),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        json.dump({"seed": args.seed, "splits": split}, f, indent=1)

    print(f"wrote {args.out}\n")
    print(f"{'':<8}{'houses':>9}{'steps':>12}{'paper houses':>15}{'paper steps':>14}")
    print("-" * 58)
    for name, members in split.items():
        steps = sum(sizes[h] for h in members)
        ph, ps = PAPER[name]
        print(f"{name:<8}{len(members):>9,}{steps:>12,}{ph:>15,}{ps:>14,}")
    print("-" * 58)
    total_steps = sum(sizes.values())
    print(f"{'total':<8}{n:>9,}{total_steps:>12,}{2500:>15,}{1_547_699:>14,}")

    overlap = set(split["train"]) & set(split["test"])
    assert not overlap, f"train/test overlap: {overlap}"
    assert sum(len(v) for v in split.values()) == n, "houses lost in the split"
    print("\nno overlap between splits, no houses dropped")


if __name__ == "__main__":
    main()
