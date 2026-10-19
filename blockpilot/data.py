"""Loading and cleaning of the 3D-Craft dataset.

A house's raw log is a list of actions:

    [tick, entity_id, [x, y, z], [block_id, meta], "P" | "B"]

Block ids are stored as signed bytes, so ids above 127 appear negative and are
normalised with `& 0xFF`. `meta` (0-15) distinguishes variants such as stair
facing and wood species; the 2019 paper discards it, so we keep it available
but do not use it for prediction targets.

Cleaning follows the paper's three steps. See research/verify_cleaning.py for
the reproduction of their published counts, and decisions/002 for why
26-connectivity is used in the component filter.
"""

from __future__ import annotations

import json
from collections import deque
from itertools import product
from pathlib import Path
from typing import Iterator, Sequence

Position = tuple[int, int, int]
BlockId = int
Placement = tuple[Position, BlockId]
Action = list

NEIGHBOURS_26 = tuple(d for d in product((-1, 0, 1), repeat=3) if d != (0, 0, 0))

MIN_PLACEMENTS = 10
DEV_HOUSE_PREFIX = "jgray"

DEFINITIONS = ("all_actions", "placements_only", "surviving_placements")


def l1(a: Position, b: Position) -> int:
    """Manhattan distance. A result of 1 means the two blocks share a face."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def iter_house_paths(root: Path) -> Iterator[Path]:
    """Yield every placed.json under `root`, sorted for reproducibility."""
    for house_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        actions_file = house_dir / "placed.json"
        if actions_file.exists():
            yield actions_file


def load_actions(path: Path) -> list[Action]:
    """Read one house's raw action log."""
    with path.open() as f:
        return json.load(f)


def placements_for_definition(
    actions: Sequence[Action], definition: str
) -> list[Placement]:
    """Ordered (position, block_id) pairs that count as placed blocks.

    all_actions           every row, place or break
    placements_only       rows where the action is "P"
    surviving_placements  rows where the action is "P" and no later action
                          touches the same position
    """
    match definition:
        case "all_actions":
            return [(tuple(a[2]), a[3][0] & 0xFF) for a in actions]
        case "placements_only":
            return [(tuple(a[2]), a[3][0] & 0xFF) for a in actions if a[4] == "P"]
        case "surviving_placements":
            seen: set[Position] = set()
            out: list[Placement] = []
            for a in reversed(actions):
                pos = tuple(a[2])
                if a[4] == "P" and pos not in seen:
                    out.append((pos, a[3][0] & 0xFF))
                seen.add(pos)
            out.reverse()
            return out
        case _:
            raise ValueError(f"unknown definition: {definition!r}")


def largest_component(positions: set[Position]) -> set[Position]:
    """Largest 26-connected component of `positions`.

    Face-only (6-connected) adjacency over-fragments, because real structures
    are often joined through terrain that never appears in the placement log.
    """
    remaining = set(positions)
    best: set[Position] = set()
    while remaining and len(remaining) > len(best):
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            x, y, z = queue.popleft()
            for dx, dy, dz in NEIGHBOURS_26:
                neighbour = (x + dx, y + dy, z + dz)
                if neighbour in remaining:
                    remaining.discard(neighbour)
                    component.add(neighbour)
                    queue.append(neighbour)
        if len(component) > len(best):
            best = component
    return best


def clean_house(path: Path) -> list[Placement] | None:
    """One house's cleaned placement sequence, or None if the house is dropped.

    Order is preserved. Houses are dropped when they are the paper authors' own
    dev data, or have fewer than MIN_PLACEMENTS blocks after cleaning.
    """
    if path.parent.name.startswith(DEV_HOUSE_PREFIX):
        return None

    ordered = placements_for_definition(load_actions(path), "surviving_placements")
    if not ordered:
        return None

    keep = largest_component({pos for pos, _ in ordered})
    ordered = [(pos, bid) for pos, bid in ordered if pos in keep]
    if len(ordered) < MIN_PLACEMENTS:
        return None
    return ordered


def iter_clean_houses(root: Path, only: set[str] | None = None):
    """Yield (house_id, placements) for houses that survive cleaning.

    Args:
        root: the houses/ directory.
        only: if given, restrict to these house ids (used with a split).
    """
    for path in iter_house_paths(root):
        house_id = path.parent.name
        if only is not None and house_id not in only:
            continue
        placements = clean_house(path)
        if placements is not None:
            yield house_id, placements


def load_split(path: Path, name: str) -> set[str]:
    """Read one split ("train" / "val" / "test") from a frozen split file."""
    with path.open() as f:
        payload = json.load(f)
    if name not in payload["splits"]:
        raise ValueError(f"unknown split {name!r}")
    return set(payload["splits"][name])
