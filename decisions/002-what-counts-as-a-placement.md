# 002 — A "placement" is a surviving placement inside the largest 26-connected component

**Date:** 2026-09-15
**Status:** Accepted

## Chose
A training/evaluation step is a `P` action that (a) is the last action at its
position, and (b) falls inside the house's largest **26-connected** component.
Houses are dropped if they are the paper authors' own dev data (`jgray_*`) or
retain fewer than 10 placements. No excavation threshold is applied.

## Alternative
- Every action in the log, place and break alike.
- Every `P` action, without the survivor filter.
- 6-connectivity (face adjacency) for the component filter, which was the
  first instinct.
- An excavation filter keyed on the break/place ratio.

## Why
Resolved empirically rather than by argument. The paper publishes two numbers
that a correct pipeline must reproduce, and they constrain different things.

**Locality (Figure 2a).** Each cleaning step raises it monotonically toward the
published 67.9% / 93.7%:

    all_actions            60.9% / 95.6%
    placements_only        66.2% / 94.4%
    surviving_placements   67.7% / 93.6%
    + component filter     68.0% / 93.7%
    paper                  67.9% / 93.7%

**Step count.** The paper's split sums to 1,547,699 steps across 2,500 houses.
Connectivity is identified by this alone:

    6-conn    1,483,203   -64,496
    18-conn   1,546,070    -1,629
    26-conn   1,548,170      +471

6-connectivity is wrong by 4%. The reason is physical: Minecraft structures are
routinely joined through terrain, which never appears in the placement log, so
face-only adjacency fragments one building into pieces and discards most of it.

Final agreement: 2,505 houses (paper 2,500), 1,548,131 placements (+0.03%),
68.0% / 93.7% locality.

Dropping `jgray_*` is on provenance, not fitting — one has 1 placement against
169 breaks and is named "remove". The <10 placement cutoff moves the total by
30 placements, so its exact value does not matter.

No excavation threshold was fitted, deliberately. Every ratio cutoff tested
undershoots the paper's count (`>5` lands at +144, `>3` at -1,217, `>2` at
-7,063). Picking `>5` because it minimises the gap would be circular. The
useful finding is that the paper's own cave filter removed very little.

## What would change my mind
- Finding the original preprocessing code, which would settle the ~5 house and
  ~432 placement residual directly.
- A downstream result that is sensitive to the residual. At 0.03% of steps it
  cannot move acc@1 measurably, so this is unlikely.
