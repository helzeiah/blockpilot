"""acc@k, the evaluation metric from Chen et al. (ICCV 2019).

The metric is easy to misread. It is NOT top-k predictions. The model makes a
single prediction, and acc@k asks whether that prediction appears anywhere in
the human's next k actions:

    correct  iff  prediction in {truth[t], truth[t+1], ..., truth[t+k-1]}

The relaxation is on the human's side, not the model's. Its purpose is to avoid
punishing a model for ordering ties: filling a wall left-to-right and
right-to-left are both human, and strict next-step matching would penalise one
arbitrarily.

A prediction is a (position, block_id) pair and BOTH must match. Position is
absolute; block_id is normalised with `& 0xFF`; `meta` is ignored, matching the
paper's 256-way block-type softmax.

Judgement calls, since the paper does not state them:

  - Evaluation starts at index 1. Index 0 has no preceding block, so there is
    no anchor for a relative prediction.
  - A predictor that lacks the history it needs returns None, which counts as
    incorrect rather than being skipped. This keeps the denominator identical
    across predictors so their numbers are comparable. It costs Naive Inertia
    about 0.16% of steps, which it cannot predict for want of two predecessors.
  - Near the end of a house, fewer than k future actions exist. The available
    ones are used.
  - Two denominators are reported. `all` counts every evaluated step.
    `in_window` counts only steps whose ground-truth position lies within
    WINDOW_RADIUS (Chebyshev/L-infinity) of the previous block, which is the
    set a model with a 7^3 output space can possibly reach.

    The paper does not say which it uses, but `in_window` reproduces its
    Naive Inertia row far more closely:

        acc@1 / acc@5 / acc@10      paper 38.7 / 47.0 / 48.3
        ours, all steps             36.8 / 44.1 / 45.9   (-1.9 / -2.9 / -2.4)
        ours, in-window only        39.9 / 47.6 / 49.3   (+1.2 / +0.6 / +1.0)

    Split randomness is ruled out: over 2,000 random 500-house draws our
    all-steps figure has mean 36.28 and sd 0.62, so 38.7 sits 3.9 sd away and
    was reached by none of them. `in_window` is therefore treated as the
    paper-comparable number, and `all` as the honest one. Report both.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Protocol, Sequence

from .data import Placement, Position, iter_clean_houses

DEFAULT_KS = (1, 5, 10)

# Chebyshev radius of the 2019 model's output space: a 7x7x7 box, D_l = 3.
WINDOW_RADIUS = 3


def chebyshev(a: Position, b: Position) -> int:
    """L-infinity distance: the largest of the three axis gaps."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


class Predictor(Protocol):
    """Streaming next-placement predictor.

    The driver calls reset() once per house, then alternates predict() and
    observe() so that predict() always sees exactly the prefix before the step
    being predicted.
    """

    def reset(self) -> None:
        """Clear per-house state."""

    def predict(self) -> Placement | None:
        """Predict the next placement, or None if there is not enough history."""

    def observe(self, placement: Placement) -> None:
        """Take the ground-truth placement for the step just predicted."""


@dataclass
class Result:
    ks: tuple[int, ...]
    n_steps: int = 0
    n_steps_in_window: int = 0
    n_correct: dict[int, int] = field(default_factory=dict)
    n_correct_in_window: dict[int, int] = field(default_factory=dict)
    n_houses: int = 0
    n_abstained: int = 0

    def __post_init__(self) -> None:
        if not self.n_correct:
            self.n_correct = {k: 0 for k in self.ks}
        if not self.n_correct_in_window:
            self.n_correct_in_window = {k: 0 for k in self.ks}

    def accuracy(self, k: int, in_window: bool = False) -> float:
        """acc@k as a percentage, over either denominator."""
        if in_window:
            n = self.n_steps_in_window
            return 100.0 * self.n_correct_in_window[k] / n if n else 0.0
        return 100.0 * self.n_correct[k] / self.n_steps if self.n_steps else 0.0

    @property
    def window_coverage(self) -> float:
        """Percentage of steps whose ground truth is reachable in-window."""
        return 100.0 * self.n_steps_in_window / self.n_steps if self.n_steps else 0.0

    def summary(self, in_window: bool = False) -> str:
        return "  ".join(
            f"acc@{k}: {self.accuracy(k, in_window):.1f}%" for k in self.ks
        )


def score_house(
    predictor: Predictor,
    placements: Sequence[Placement],
    ks: Sequence[int],
    result: Result,
) -> None:
    """Run one house through a predictor, accumulating into `result`."""
    predictor.reset()
    predictor.observe(placements[0])

    max_k = max(ks)
    for i in range(1, len(placements)):
        prediction = predictor.predict()
        reachable = chebyshev(placements[i][0], placements[i - 1][0]) <= WINDOW_RADIUS

        result.n_steps += 1
        if reachable:
            result.n_steps_in_window += 1

        if prediction is None:
            result.n_abstained += 1
        else:
            future = placements[i : i + max_k]
            for k in ks:
                if prediction in future[:k]:
                    result.n_correct[k] += 1
                    if reachable:
                        result.n_correct_in_window[k] += 1
        predictor.observe(placements[i])


def evaluate(
    predictor: Predictor,
    root: Path,
    house_ids: set[str] | None = None,
    ks: Sequence[int] = DEFAULT_KS,
) -> Result:
    """Score a predictor over every house in `house_ids`."""
    result = Result(ks=tuple(ks))
    for _house_id, placements in iter_clean_houses(root, only=house_ids):
        score_house(predictor, placements, ks, result)
        result.n_houses += 1
    return result
