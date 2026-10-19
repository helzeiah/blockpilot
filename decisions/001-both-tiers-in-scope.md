# 001 — Both tier A and tier B are in scope; hybrid only if measured as necessary

**Date:** 2026-08-23
**Status:** Accepted

## Chose
Pursue segment completion (tier A: "finish the row of panes I started") and whole-build
suggestion (tier B: "here is a complete 150-block structure") as co-equal product goals.
Start with a single next-block-prediction model. Add a second mechanism only if measured
rollout degradation requires it.

## Alternative
- Commit to a hybrid architecture up front (e.g. retrieval for whole builds + a learned
  model for segments).
- Ship tier A only, and treat whole-build suggestion as a separate future project.

## Why
**Product:** both capabilities are core to the value proposition. Tier A is the everyday
usefulness (the reason someone leaves the mod switched on); tier B is the demonstration of
power. Neither is being traded away.

**Technical:** VoxelCNN's published numbers say a next-block model cannot naively produce
coherent large structures. Normalized MTC of 23.2% means roughly one in four of its
placements is wrong when completing a house, and CCA of 11.7 means it averages under a
dozen correct blocks before its first mistake. Rolling such a model out 150 steps
compounds those errors. So *some* additional mechanism is likely required.

But the right mechanism — retrieval over training structures, a holistic one-shot
generator, or part-based prediction (wall / roof / door per step) — depends on *how*
rollout fails, and that is unmeasured. Nobody has published it, including the original
authors. Choosing a hybrid design now means guessing the shape of an unmeasured problem.

Counter-evidence worth holding: in language modeling, single-line and whole-function
completion came from one model with one set of weights. What made that work was scale and
context length, not a change of architecture. The asymmetry is that a wrong token stays
plausible while a wrong block puts a visible hole in a wall that all later predictions
then condition on.

## What would change my mind
- **Toward a single model:** if one model with longer context and a modern training recipe
  reaches a CCA high enough to cover a typical build segment (~50+ blocks), no hybrid is
  needed.
- **Toward two separate models:** if rollout degrades within the first ~5 blocks, the two
  capabilities are fundamentally different problems and should not share weights.
- **Toward retrieval specifically:** if retrieval beats the learned model on whole-build
  suggestion by a wide margin, generalization matters less here than I assume.
