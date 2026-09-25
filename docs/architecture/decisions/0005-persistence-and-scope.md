# ADR-0005: Persistence, Position Computation, and v1 Scope

Status: Accepted — confirmed in architecture review (2026-09-25); no change
to the decision, reviewed on the merits of read-vs-materialized cost/benefit
Date: 2026-09-25

## Context

The product brief scopes Atlas as local, single-user, and without
authentication. It doesn't state whether positions should be stored as
materialized state or derived on demand from transaction history.

## Decision

- Persist only **assets** and **transactions** as source-of-truth records in
  SQLite.
- Compute **positions, average price, realized/unrealized P&L, and
  allocation on read**, by replaying/aggregating the transaction history
  through the domain layer. No materialized "current position" table in v1.
- No authentication or user table in v1: the database holds a single
  implicit user's data.
- One portfolio per installation in v1 (no multi-portfolio/account
  grouping), matching the brief's singular framing ("their portfolio").

## Alternatives Considered

- **Materialized/cached positions**, updated incrementally on each
  transaction write. Rejected for v1: adds complexity (cache invalidation,
  keeping derived state consistent with the transaction log) with no
  demonstrated need — a single local user's transaction history is small
  enough to recompute on every read cheaply. Can be introduced later if
  performance requires it, without changing the domain's public behavior.
- **Multi-portfolio data model from the start.** Rejected for v1 as
  unrequested scope; noted as something the domain model shouldn't be
  needlessly hard to extend into later, but not built now.

## Consequences

- Simpler write path (transactions are append-only-ish; no derived state to
  keep in sync).
- Read path does more work per request, which is an acceptable trade-off at
  single-user local scale.
- If multi-portfolio support is ever requested, the transaction/asset schema
  will need a portfolio identifier added — a schema migration, not a full
  redesign, if the domain layer keeps this in mind.
