# ADR-0002: Technology Stack

Status: Accepted, except the frontend choice — superseded by
[ADR-0007](./0007-frontend-simplification-and-persistence-rationale.md)
Date: 2026-09-25

## Context

Atlas needs a concrete stack to let the engineering team start work. The
product brief sets no technology constraints beyond "local web application."
The repository lives under a Python-oriented workspace and the project's
stated purpose is exploring agentic software engineering workflows, which
benefits from a stack with strong typing/validation and easy testability.

## Decision

- **Backend language**: Python.
- **API framework**: FastAPI — gives request/response validation
  (via Pydantic schemas) and automatic OpenAPI schema generation practically
  for free, which keeps the API contract close to the code and eases
  integration testing.
- **Persistence**: SQLite, accessed through SQLAlchemy. Zero-config,
  single-file, fits a local single-user app; SQLAlchemy gives a clean
  repository-pattern boundary and an upgrade path to another RDBMS later if
  ever needed.
- ~~**Frontend**: TypeScript + React, as a single-page application consuming
  the REST API. TypeScript's static typing pairs naturally with a documented
  JSON contract.~~ **Superseded by
  [ADR-0007](./0007-frontend-simplification-and-persistence-rationale.md):**
  plain HTML/CSS/vanilla JavaScript, kept here for the historical record of
  why React was picked first.
- **Backend testing**: pytest.

## Alternatives Considered

- **Flask** instead of FastAPI: lighter, but lacks built-in request
  validation and OpenAPI generation, which would need to be added manually.
- **Django (+ DRF)**: more batteries-included, but heavier than an
  educational single-user project needs, and its ORM-centric style
  encourages coupling business logic to the framework — at odds with
  ADR-0001.
- **PostgreSQL** instead of SQLite: unnecessary operational overhead (a
  running server process) for a local single-user app with no concurrent
  writers.
- **Plain HTML/JS or server-rendered templates** instead of a SPA: would
  blur the frontend/backend boundary the brief implicitly wants (business
  logic not depending on the UI implies a real API boundary exists).
- **Vue/Svelte** instead of React: equally valid; React chosen for
  ubiquity and tooling maturity, not a strong technical requirement. This is
  the most easily revisited choice in this ADR.

## Consequences

- Backend and frontend are decoupled by a REST contract, allowing them to be
  worked on independently (including by different agents/developers).
- SQLite is not suitable if Atlas ever needs concurrent multi-user access;
  that would require revisiting this decision (out of scope for v1, per the
  product brief).
- FastAPI's generated OpenAPI schema should be treated as authoritative once
  the backend exists; `API_CONTRACT.md` should be kept in sync with it.
