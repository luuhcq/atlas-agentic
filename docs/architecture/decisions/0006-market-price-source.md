# ADR-0006: Market Price Acquisition Strategy

Status: Proposed — pending product decision
Date: 2026-09-25

## Context

Unrealized P&L, market value, and allocation-by-value all require a current
price per asset. The product brief lists these as required views but does
not say where current prices come from. Atlas is described as a local
application, which raises a genuine question about whether it's expected to
reach the internet for live market data at all.

## Decision

Model price lookup behind a `MarketPriceProvider` port (see ADR-0003) so the
domain layer is unaffected by which source is ultimately chosen. **The
specific v1 source is not decided by this ADR** — it is an open product
question (see ARCHITECTURE.md §8) with at least these options:

1. Manual entry — user inputs/updates current prices themselves.
2. External market data API — requires outbound internet access and a data
   source decision (which is itself a scope change for a "local" app).
3. Fallback to last transaction price when no current price is available —
   usable as an interim/default behavior regardless of which of the above is
   chosen, so unrealized P&L degrades gracefully instead of failing.

The API contract (`API_CONTRACT.md`) already returns `null` for
price-dependent fields, so the frontend can be built before this is
resolved.

## Alternatives Considered

- **Decide now without product input.** Rejected: this is a product/scope
  decision (does Atlas require internet access?), not purely technical, and
  the brief instructs identifying rather than silently resolving such
  ambiguity.
- **Block all portfolio-value work until resolved.** Rejected: positions,
  quantities, and average cost (which don't need current price) can be
  fully implemented and tested now; only current-price-dependent fields are
  blocked.

## Consequences

- Unrealized P&L, market value, and value-based allocation cannot be
  finished until this decision is made.
- Everything else in the brief's scope is unaffected and can proceed.
