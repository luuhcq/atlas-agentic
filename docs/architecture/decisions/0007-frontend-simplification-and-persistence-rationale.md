# ADR-0007: Frontend Simplification and Persistence Boundary Rationale

Status: Accepted
Date: 2026-09-25

## Context

Architecture review of the initial proposal (ADR-0002) challenged two
stack-level choices:

1. Whether a React + TypeScript SPA was warranted for a local, educational,
   single-user application whose product principles explicitly prioritize
   simplicity, compared with plain HTML/CSS/JavaScript.
2. Whether SQLAlchemy was justified given that the current data model
   (assets, transactions) does not itself require an ORM.

## Decision

1. **Frontend**: replace React + TypeScript with plain HTML, CSS, and
   vanilla JavaScript. The frontend remains a separate static artifact that
   talks to the backend exclusively through the REST API documented in
   `API_CONTRACT.md` — that contract, not the frontend's implementation
   technology, is what lets frontend and backend be built and tested
   independently (including by different agents). Removing React removes a
   build toolchain, a component framework, and an npm dependency tree
   without weakening that boundary.
2. **Persistence**: SQLAlchemy + SQLite is retained. This is an explicit
   exception to "pick the simplest thing the current schema needs" — the
   two-table schema alone would be served just as well by the standard
   library's `sqlite3` module. SQLAlchemy is kept because Atlas is also an
   experiment in multi-agent software engineering, and a well-defined
   repository/persistence boundary (ADR-0003) is valuable precisely because
   it can be implemented and tested independently of the domain and API
   layers by a separate agent. No further persistence abstractions
   (unit-of-work, generic repository base classes, query builders beyond
   SQLAlchemy's own, migration tooling beyond what's needed) should be added
   beyond what implementing that boundary requires.

## Alternatives Considered

- **Keep React + TypeScript.** Rejected: the original justification
  (ubiquity, typed contract, tooling maturity) is a preference for
  industry-standard tooling, not a justification against the brief's own
  simplicity principle. The SPA's build tooling and framework concepts
  (component lifecycle, state management, bundling) are unrelated to the
  project's actual learning goals (finance domain logic, agentic workflow)
  and add cognitive load for a student for no offsetting benefit at this
  UI's scale.
- **Server-rendered templates** (e.g. FastAPI + Jinja2) instead of a
  separate static frontend. Rejected: this would blur or eliminate the
  REST API's role as a UI-facing contract, weakening the property that lets
  frontend and backend be developed independently — a property that matters
  for this project's stated multi-agent purpose even though it wouldn't
  matter for a solo developer.
- **Replace SQLAlchemy with raw `sqlite3`.** This would be the leaner choice
  judged purely against the current schema, and remains worth reconsidering
  if the ORM ever becomes friction rather than structure. Not adopted now
  because the repository boundary it supports is being deliberately
  exercised as part of this project's secondary goal (practicing
  independent multi-agent implementation), not carried as incidental
  complexity.

## Consequences

- The frontend has no build step; it can be served as static files (e.g.
  directly by FastAPI, or any static file server) and opened/tested in a
  browser without tooling.
- Frontend and backend agents continue to coordinate solely through
  `API_CONTRACT.md`; no shared framework code exists between them.
- SQLAlchemy usage should stay minimal: plain declarative models and
  session-scoped repository classes implementing the interfaces from
  ADR-0003 — nothing more elaborate.
- This ADR supersedes only the frontend portion of ADR-0002; the backend
  language, API framework, persistence engine, and testing choices in
  ADR-0002 stand, with the persistence rationale clarified here.
