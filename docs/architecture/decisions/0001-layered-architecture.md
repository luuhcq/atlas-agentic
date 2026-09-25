# ADR-0001: Layered Architecture with Isolated Domain

Status: Accepted
Date: 2026-09-25

## Context

The product brief requires that business logic (financial calculations) be
deterministic, testable, and independent of the UI. Atlas is a local,
single-user web app with a REST-consuming frontend.

## Decision

Structure Atlas as four layers, with dependencies pointing inward:

- **Frontend** — presentation only, talks to the backend via REST (the
  specific frontend technology is decided in ADR-0002/ADR-0007 and doesn't
  affect this layering decision).
- **API layer** — HTTP adapter (routing, validation, error mapping).
- **Domain layer** — pure business logic (entities, calculations). No
  dependency on the API framework or the persistence framework.
- **Persistence layer** — concrete data access, implementing interfaces
  (ports) the domain defines.

The domain layer must never import from the API layer or from a specific
persistence technology. The API and persistence layers depend on the domain,
not the other way around.

## Alternatives Considered

- **Single monolithic backend module** (routes calling the ORM directly,
  calculations inline in route handlers). Rejected: it would couple
  business logic to both HTTP and the ORM, directly violating the brief's
  requirement that business logic not depend on the UI, and making unit
  testing of financial calculations harder.
- **Full hexagonal/clean architecture with strict layer packages and
  dependency-injection framework.** Considered but judged more ceremony than
  an educational, single-user project needs. This ADR adopts the same
  dependency-direction principle without mandating a specific DI framework
  or package-per-layer rigor.

## Consequences

- Enables unit-testing the domain layer (position/P&L/allocation
  calculations) without a database or HTTP server.
- Adds a small amount of indirection (interfaces between domain and
  persistence) compared to calling the ORM directly.
- Frontend and backend can evolve independently as long as the REST contract
  is honored.
