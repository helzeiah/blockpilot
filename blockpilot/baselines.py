"""Non-learned baselines from Chen et al. (ICCV 2019), Table 1.

    Naive Inertia   acc@1 38.7   acc@5 47.0   acc@10 48.3

These exist to validate the evaluation harness. They contain no learned
parameters, so if the harness is correct their numbers are reproducible exactly.
"""

from __future__ import annotations

from .data import Placement, Position


class NaiveInertia:
    """Continue in a straight line with the same block type.

        position_{t+1} = 2 * position_t - position_{t-1}
        block_{t+1}    = block_t

    Encodes the observation that people lay blocks in runs: having moved one
    step in some direction, the next move is most often another step the same
    way. Needs two predecessors, so it abstains on the first predicted step of
    every house.
    """

    def __init__(self) -> None:
        self.previous: Position | None = None
        self.current: Position | None = None
        self.block: int | None = None

    def reset(self) -> None:
        self.previous = None
        self.current = None
        self.block = None

    def predict(self) -> Placement | None:
        if self.previous is None or self.current is None or self.block is None:
            return None
        extrapolated = (
            2 * self.current[0] - self.previous[0],
            2 * self.current[1] - self.previous[1],
            2 * self.current[2] - self.previous[2],
        )
        return (extrapolated, self.block)

    def observe(self, placement: Placement) -> None:
        position, block = placement
        self.previous = self.current
        self.current = position
        self.block = block
