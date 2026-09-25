# Atlas — Technical Architecture

Status: Accepted (v1), pending items noted in §8
Last reviewed: 2026-09-25 (architecture review — see [ADR-0007](./decisions/0007-frontend-simplification-and-persistence-rationale.md) and [ADR-0004](./decisions/0004-cost-basis-method.md))
Owner: Software Architecture
Related: [API Contract](./API_CONTRACT.md) · [Architecture Decision Records](./decisions/)

## 1. Purpose and Scope

This document describes the initial technical architecture for Atlas, a local,
single-user web application for personal investment portfolio management, as
defined in the product brief (see connected `product-brief` note).

It covers system boundaries, layering, technology choices, and the rationale
behind them. It does not specify UI design, does not implement code, and does
not fix product scope beyond what the brief already states.

## 2. Product Recap (for context)

Atlas must let a single local user:

- register financial assets;
- record buy/sell transactions (manually and via CSV import);
- view current positions, average acquisition price, portfolio value;
- view realized and unrealized profit/loss;
- visualize allocation;
- inspect transaction history.

Product principles that directly shape this architecture:

- educational/experimental project, local-only, single-user, no auth (v1);
- financial calculations must be **deterministic and testable**;
- business logic must **not depend on the UI**;
- prefer simplicity over unnecessary complexity.

## 3. High-Level Architecture

Atlas is a classic 3-tier application with an explicit, isolated domain layer.
The guiding structure is layered architecture with ports & adapters at the
edges (see [ADR-0001](./decisions/0001-layered-architecture.md) and
[ADR-0003](./decisions/0003-domain-isolated-via-ports-and-adapters.md)).

```
                        ┌─────────────────────────┐
                        │   Frontend                │
                        │   Plain HTML/CSS/JS       │
                        │   (static, no build step) │
                        └───────────┬─────────────┘
                                    │ HTTP/JSON (REST, versioned)
                                    ▼
                        ┌─────────────────────────┐
                        │   API Layer (FastAPI)    │
                        │   - routing               │
                        │   - request/response      │
                        │     validation (schemas)  │
                        │   - HTTP error mapping    │
                        └───────────┬─────────────┘
                                    │ calls
                                    ▼
                        ┌─────────────────────────┐
                        │   Domain / Business Logic │
                        │   (pure Python, no I/O)   │
                        │   - Asset, Transaction     │
                        │   - Position aggregation   │
                        │   - Cost basis / P&L       │
                        │   - Allocation calculation │
                        └──────┬───────────┬────────┘
                               │           │
                     (port)    │           │  (port)
              Repository ports │           │  CSV Importer /
                               │           │  Market Price Provider
                               ▼           ▼
                  ┌───────────────────┐  ┌──────────────────────────┐
                  │ Persistence        │  │ External data adapters    │
                  │ SQLAlchemy + SQLite│  │ CSV parser, price source   │
                  └───────────────────┘  └──────────────────────────┘
```

### Layers

1. **Frontend** — plain HTML, CSS, and vanilla JavaScript; presentation only,
   no build step. Talks to the backend exclusively through the documented
   REST API. Owns no business rules (e.g. it does not compute P&L; it
   displays what the API returns). See
   [ADR-0007](./decisions/0007-frontend-simplification-and-persistence-rationale.md).
2. **API layer** — thin HTTP adapter. Validates input shape, translates
   HTTP requests into domain calls, translates domain results/errors into
   HTTP responses. Contains no financial calculation logic.
3. **Domain layer** — the core of the system. Plain Python objects and
   functions with no dependency on FastAPI, SQLAlchemy, or HTTP. Contains all
   business rules: recording transactions, computing positions, average
   acquisition price, realized/unrealized P&L, allocation breakdowns. This is
   the layer the product brief's "deterministic and testable" requirement is
   about, and it is unit-testable in complete isolation (no DB, no HTTP).
4. **Persistence layer** — repository implementations (SQLAlchemy over
   SQLite) behind repository interfaces (ports) defined by the domain layer.
   The domain depends on the interface, not on SQLAlchemy.
5. **External data adapters** — CSV import and market price lookup are
   modeled as ports the domain depends on, with concrete adapters supplied
   from outside. This isolates two genuinely uncertain integration points
   (see open questions) without blocking the rest of the design.

This structure satisfies the brief's explicit constraint that business logic
must not depend on the UI, and makes the domain layer independently testable,
per the assigned architectural responsibility to "consider testability when
designing components."

## 4. Technology Stack

See [ADR-0002](./decisions/0002-technology-stack.md) and
[ADR-0007](./decisions/0007-frontend-simplification-and-persistence-rationale.md)
for full rationale and alternatives considered. Summary:

| Concern            | Choice                                   |
|---------------------|-------------------------------------------|
| Backend language    | Python                                    |
| API framework       | FastAPI                                   |
| Domain layer         | Plain Python (no framework dependency)   |
| Persistence          | SQLite, accessed via SQLAlchemy (kept deliberately as an independently-implementable boundary, not because the schema requires an ORM — see ADR-0007) |
| Frontend             | Plain HTML, CSS, vanilla JavaScript — static, no build step (see ADR-0007) |
| API style            | REST, JSON, versioned (`/api/v1`)        |
| Testing              | pytest (backend); manual/browser-based checks for the frontend, given it has no framework or build step |

## 5. Proposed Repository Layout

This is a recommendation for the engineering team, not an implementation:

```
atlas-agentic/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers, request/response schemas
│   │   ├── domain/         # entities, services, calculation logic (pure)
│   │   ├── ports/          # repository & adapter interfaces (abstract)
│   │   ├── adapters/       # SQLAlchemy repos, CSV importer, price provider
│   │   └── main.py
│   └── tests/
│       ├── unit/           # domain layer, no DB/HTTP
│       └── integration/    # API + persistence
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/                 # plain JS modules calling the REST API
└── docs/
    └── architecture/
```

## 6. Key Cross-Cutting Decisions

- **Positions computed on read, not maintained as materialized state in v1**
  — for a single-user local dataset, recomputing positions/P&L from the
  transaction history at query time is simpler and always consistent. This
  can be revisited (e.g. materialized/cached positions) if performance ever
  requires it. See [ADR-0005](./decisions/0005-persistence-and-scope.md).
- **No authentication in v1**, per product brief. The API has no user
  concept; all data belongs to the single local user.
- **Single currency, single portfolio assumed for v1** (see Open Questions).
- **Cost-basis method — approved product decision**: moving weighted-average
  cost is used for average acquisition price and realized P&L. Each buy
  recalculates the running average cost; each sell realizes P&L against the
  average cost immediately before that sale and does not itself change the
  average cost of the remaining position; a sell for more units than
  currently held must be rejected by the domain layer. See
  [ADR-0004](./decisions/0004-cost-basis-method.md).

## 7. Testability

- Domain services take plain data in and return plain data out; they can be
  unit-tested with in-memory fakes for the repository/port interfaces —
  no database or HTTP server required.
- Repository, CSV importer, and price provider are all defined as
  interfaces (ports) the domain depends on, so adapters can be swapped for
  test doubles.
- The API layer is tested separately (integration tests) to verify HTTP
  contract compliance (status codes, payload shapes) against the documented
  [API contract](./API_CONTRACT.md).
- CSV import logic is tested against fixture files, independent of the rest
  of the system.

## 8. Open Questions (do not block starting architecture/documentation work)

These are product/requirements ambiguities identified during this design
pass. None of them prevent the layering, boundaries, or stack decisions
above; they do need a decision before the affected feature is implemented.

Resolved since the last review: cost-basis method (see ADR-0004), frontend
technology, and the SQLAlchemy-vs-schema-size question (see ADR-0007).
Remaining open items:

1. **Source of current market prices** for unrealized P&L and total
   portfolio value — manual entry, external market data API, or another
   mechanism? This also determines whether Atlas needs outbound internet
   access, which is non-trivial for a "local" app. Modeled behind a port
   (see [ADR-0006](./decisions/0006-market-price-source.md)) so the
   decision doesn't block architecture, but it blocks implementing
   unrealized P&L / current value.
2. **CSV import format** — the brief doesn't name a broker/source format.
   Proposed: define one documented generic Atlas CSV schema for v1 (see API
   contract) and defer broker-specific mapping.
3. **Currency handling** — brief doesn't mention multi-currency. Assumed:
   single currency for all assets and totals in v1.
4. **Portfolio scope** — brief refers to "their portfolio" in the singular;
   assumed one portfolio per installation in v1 (no multi-portfolio/account
   grouping). Domain model should not make this hard to extend later, but v1
   will not implement it.
5. **Asset identity/uniqueness** — no rule given for what makes two assets
   the same (e.g. ticker symbol vs. symbol+exchange). Needs a decision before
   the asset registration endpoint is finalized in detail.

## 9. Non-Goals for v1

- Authentication/authorization.
- Multi-user or multi-portfolio support.
- Real-time price streaming.
- Deployment/hosting concerns beyond local execution.
