# Atlas — Project-Wide Agent Instructions

This file applies to every agent working anywhere in this repository,
regardless of assigned role (architecture, backend, frontend, review,
testing, etc.). Role-specific instructions (e.g. under `.maestri/roles/`)
add to this, they don't replace it.

## What Atlas Is

A local, single-user web application for personal investment portfolio
management, built as an exploration of multi-agent software engineering
(see `README.md`). Product scope lives in the connected `product-brief`
note; technical architecture lives in `docs/architecture/`.

## Before Making Changes

- Read `docs/architecture/ARCHITECTURE.md` and the relevant ADRs in
  `docs/architecture/decisions/` before making a change that touches system
  structure, the API contract, or the data model.
- Check the API contract (`docs/architecture/API_CONTRACT.md`) before
  changing any backend endpoint's request/response shape; keep it in sync
  with the implementation (or with the generated OpenAPI schema once one
  exists).
- Check `docs/architecture/ARCHITECTURE.md` §8 (Open Questions) before
  implementing a feature that depends on one of them (market price source,
  CSV format, currency, portfolio scope, asset identity). If your task
  requires resolving one, do so explicitly and record it (update the
  relevant ADR's status, don't just code around it).

## Architectural Boundaries (do not violate)

- The **domain/business-logic layer must not import** the API framework
  (e.g. FastAPI) or the ORM (e.g. SQLAlchemy) directly. It depends on
  interfaces ("ports"); concrete I/O lives in adapters. See ADR-0001 and
  ADR-0003.
- The **frontend must not implement financial calculations** (position
  aggregation, cost basis, P&L, allocation weights). It renders what the
  API returns. See ADR-0001.
- No authentication/user model in v1, per the product brief — don't add one
  speculatively.

## Business Rules (approved, not architect assumptions)

- Cost basis is **moving weighted-average cost** (ADR-0004): every buy
  recalculates the asset's running average cost; a sell realizes P&L against
  the average cost immediately before that sale and does not change the
  average cost of the remaining position.
- A **sell for more units than are currently held must be rejected** by the
  domain layer (not only validated at the API boundary) — see ADR-0004 and
  the `insufficient_position` error in `API_CONTRACT.md`.

## Working Conventions

- Prefer simple, direct solutions over speculative flexibility — this is an
  educational project (see product brief's "Product Principles").
- Don't introduce a new dependency, framework, or service without recording
  the reason (an ADR entry, or at minimum a clear commit message rationale).
- Don't silently change product scope. If a requirement seems ambiguous or
  missing, say so explicitly (in the PR/commit/response) rather than
  inventing an interpretation and moving on — this mirrors the product
  brief's own instruction to identify ambiguity rather than silently resolve
  it.
- Domain-layer code (calculations, entities) must be covered by unit tests
  that don't require a database or HTTP server. API-layer changes should
  have integration tests against the documented contract.
- Don't claim something works, was tested, or was validated unless you
  actually ran it and observed the result. State clearly what was and
  wasn't verified.
- Keep changes scoped to the task at hand; avoid incidental edits to
  unrelated files.

## Documentation Upkeep

When a change affects architecture, the API contract, or a previously
recorded decision:

- Update `docs/architecture/ARCHITECTURE.md` and/or
  `docs/architecture/API_CONTRACT.md` in the same change.
- Add a new ADR (see `docs/architecture/decisions/README.md` for the
  template) rather than editing history into an old one, unless you are
  fixing a factual error in that same ADR. A decision that reverses a prior
  one should mark the old ADR as "Superseded by ADR-XXXX."
