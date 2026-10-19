# 003 — acc@k is reported over two denominators, with in-window as the paper-comparable one

**Date:** 2026-09-25
**Status:** Accepted

## Chose
Report `acc@k` twice:

- **in_window** — only steps whose ground-truth position lies within Chebyshev
  distance 3 of the previous block, i.e. the 7x7x7 box a model with the 2019
  output space can reach. This is the number compared against the paper.
- **all** — every evaluated step. The honest number, and the one our own
  models are compared against each other on.

## Alternative
- Report only `all`, and accept that our numbers sit ~2 points below the
  paper's for reasons we cannot explain.
- Report only `in_window`, and quietly adopt a convention that flatters every
  result by dropping the hardest 8% of steps.

## Why
The paper never states its denominator. Implementing Naive Inertia exactly as
described (`lambda_{t+1} = 2*lambda_t - lambda_{t-1}`, block type unchanged)
and scoring every step gives 36.8%, against a published 38.7%.

Split randomness was ruled out first. Over 2,000 random 500-house draws the
all-steps figure has mean 36.28 and sd 0.62; 38.7 sits 3.93 sd away and was
reached by none of them. The gap is definitional, not sampling noise.

Restricting to in-window steps fits the published row far better across every k:

                          acc@1    acc@5   acc@10    mean |error|
    paper                  38.7     47.0     48.3
    ours, all steps        36.8     44.1     45.9           2.4
    ours, in-window        39.9     47.6     49.3           0.9

This is also consistent with the paper's own framing: its model predicts a
position inside a 7^3 box, so steps whose answer lies outside that box are
unpredictable by construction and were plausibly excluded.

Both are kept because each answers a different question. `in_window` answers
"are we beating the published baseline on their terms". `all` answers "how good
is this model actually", and it is the one that matters for the product, since
a real user's next block is sometimes across the room.

Window coverage is 92.2% of steps, close to the paper's stated "over 90%".

## What would change my mind
- Recovering the original evaluation code, which would replace this inference
  with a fact.
- A cleaning change that moves the all-steps figure onto 38.7 without the
  restriction, which would mean the gap was cleaning rather than denominator.
