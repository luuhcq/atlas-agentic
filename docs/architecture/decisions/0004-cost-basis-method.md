# ADR-0004: Cost-Basis Method for Average Price and Realized P&L

Status: Accepted — approved product decision
Date: 2026-09-25 (proposed as a provisional default; confirmed as a product
decision in architecture review the same day)

## Context

Computing average acquisition price and realized profit/loss requires a
cost-basis method (e.g. weighted-average cost, FIFO, LIFO). The product
brief required these figures but did not specify the method. This was
initially recorded as an architect's provisional default, flagged for
product confirmation rather than silently assumed. It has since been
reviewed and confirmed as an explicit product decision, including the
specific mechanics for sell transactions.

## Decision

Atlas uses **moving weighted-average cost**:

- Each **buy** recalculates a single running (moving) weighted-average cost
  for the asset, combining the existing held quantity/cost with the new
  purchase.
- Each **sell**:
  - realizes profit/loss against the weighted-average cost as it stood
    immediately **before** that sale;
  - does **not** itself change the average cost of the remaining position;
  - must be **rejected** if the sell quantity exceeds the quantity currently
    held for that asset (no short positions; see also `API_CONTRACT.md`,
    which documents this as a validation error on
    `POST /api/v1/transactions`).

This is the simplest method to implement deterministically and is commonly
used for personal portfolio tracking. The domain interfaces should not
hard-code assumptions that would make switching methods (e.g. to FIFO)
require a redesign of surrounding layers, but the v1 implementation is
built against average cost as specified above, not as a placeholder.

## Alternatives Considered

- **FIFO** (first-in, first-out): a common tax-accounting method in some
  jurisdictions; requires tracking individual purchase lots rather than a
  single running average, adding complexity not requested by the brief and
  not chosen by the product decision.
- **LIFO**: rarely used for personal investment tracking; no indication it's
  needed.
- **Leaving the method unresolved / blocking on product decision**: this was
  the original alternative to defaulting, and is no longer relevant now that
  the product owner has made an explicit decision — recorded here for
  historical context on how this ADR reached its current state.

## Consequences

- Realized P&L and average price figures reflect moving weighted-average
  cost accounting, not FIFO/LIFO. Implementing lot-based accounting later
  (e.g. for tax-accurate reporting) would require reworking the domain
  calculation, not just presentation, and could change historical figures.
- The domain layer must enforce the oversell rejection rule directly (not
  just at the API validation layer), since it is a business invariant, not
  an input-shape check.
- Because positions are computed on read from the transaction log (see
  ADR-0005), the moving average is recomputed by replaying transactions in
  date order each time, rather than stored as mutable per-asset state —
  keeping the calculation itself stateless and easy to unit test.
