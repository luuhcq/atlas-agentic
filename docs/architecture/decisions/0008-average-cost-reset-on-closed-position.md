# ADR-0008: Average Cost Resets to Zero on a Fully Closed Position

Status: Accepted — approved product decision
Date: 2026-09-25

## Context

ADR-0004 specifies moving weighted-average cost mechanics for buys and
sells, but left one case unaddressed: what `average_cost` should be once a
sell brings the held quantity for an asset down to exactly zero (the
position is fully closed).

This gap surfaced during review of the first engineering increment
(`backend/app/domain/positions.py`, the pure domain position calculator),
where it had to be decided one way or another to make the calculation total.
The product owner has now resolved it explicitly.

## Decision

When a sell reduces an asset's held quantity to **0**, `average_cost` for
that asset **resets to 0** — it is not retained at its last historical
value.

This applies only to the exact-zero case. It does not change any mechanic
already specified in ADR-0004: a sell still realizes P&L against the
average cost as it stood immediately before that sale, and a sell for more
units than currently held is still rejected.

If a new buy is later recorded for the same asset after its position was
fully closed, the moving average restarts from that buy, as if the asset
had no cost-basis history — consistent with there being no held position to
average against.

## Alternatives Considered

- **Retain the last historical average cost after the position closes.**
  Rejected: a flat (zero-quantity) position has no current cost basis to
  speak of — "average cost" describes the cost of units currently held.
  Keeping a stale non-zero value risks a future consumer of this field
  (a UI, a report, a later calculation) misreading it as a live, meaningful
  figure rather than a leftover from a closed position.
- **Leave `average_cost` undefined/null when quantity is 0.** Considered,
  but rejected in favor of a concrete `0`: the field is typed and consumed
  as a number (see `API_CONTRACT.md`), and `0` is both simpler for callers
  to handle and consistent with there being nothing to average.

## Consequences

- This clarifies and extends ADR-0004; it does not reverse or conflict with
  any of its mechanics.
- `docs/architecture/API_CONTRACT.md`'s description of `average_price` under
  `GET /api/v1/portfolio/positions` is updated to state this explicitly.
- The domain position calculator must treat "quantity reaches 0" as an
  explicit reset point for `average_cost`, not merely stop updating it.
