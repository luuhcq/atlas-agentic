# ADR-0003: Domain Isolated from I/O via Ports & Adapters

Status: Accepted
Date: 2026-09-25

## Context

Two capabilities Atlas needs — CSV import and current market prices — depend
on data sources that are either unspecified (CSV format) or entirely
undecided (where prices come from; see ADR-0006). The domain layer (position
aggregation, cost basis, P&L) must not be blocked by, or rewritten because
of, decisions made about these external sources later.

## Decision

Define narrow interfaces ("ports") owned by the domain layer for anything
that reaches outside the process:

- `TransactionRepository` — persistence of assets/transactions.
- `CsvTransactionImporter` — parses an external file into domain
  transactions.
- `MarketPriceProvider` — returns a current price for an asset (or "no
  price available").

Concrete implementations ("adapters" — SQLAlchemy repository, a CSV parser
for the schema in `API_CONTRACT.md`, and whatever price source is chosen per
ADR-0006) live outside the domain layer and are supplied to it.

## Alternatives Considered

- **Call SQLAlchemy/CSV parsing directly from domain services.** Rejected:
  couples the domain to specific I/O technology and makes unit testing
  require a database or real files.
- **Defer this abstraction until the price source is decided.** Rejected:
  the cost of defining the interface now is low, and it lets domain-layer
  work (position/P&L calculation) proceed in parallel with, and independent
  of, the external-integration decisions in ADR-0006 and the CSV format
  question.

## Consequences

- Domain services are testable with in-memory fakes for all three ports.
- Adding or swapping a price source later (manual entry → external API, or
  vice versa) does not require changing domain logic, only the adapter.
- Slightly more upfront structure (interfaces + implementations) than
  calling libraries directly — judged proportionate given the brief's
  explicit testability requirement.
