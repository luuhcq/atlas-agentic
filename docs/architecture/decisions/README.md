# Architecture Decision Records (ADRs)

This directory records significant architectural decisions for Atlas: what
was decided, why, and what alternatives were considered. Keep records short
and factual.

## Index

| ID | Title | Status |
|----|-------|--------|
| [0001](./0001-layered-architecture.md) | Layered architecture with isolated domain | Accepted |
| [0002](./0002-technology-stack.md) | Technology stack | Accepted, except frontend — see 0007 |
| [0003](./0003-domain-isolated-via-ports-and-adapters.md) | Domain isolated from I/O via ports & adapters | Accepted |
| [0004](./0004-cost-basis-method.md) | Cost-basis method for P&L (moving weighted-average) | Accepted — approved product decision |
| [0005](./0005-persistence-and-scope.md) | Persistence, positions computed on read, v1 scope | Accepted |
| [0006](./0006-market-price-source.md) | Market price acquisition strategy | Proposed — pending product decision |
| [0007](./0007-frontend-simplification-and-persistence-rationale.md) | Frontend simplification and persistence boundary rationale | Accepted |
| [0008](./0008-average-cost-reset-on-closed-position.md) | Average cost resets to zero on a fully closed position | Accepted — approved product decision |

## When to add a new ADR

Add one when a decision meaningfully constrains future work: choice of
technology, a boundary between components, a data model commitment, or a
reversal of a previous decision. Skip it for routine implementation details.

## Template

```markdown
# ADR-XXXX: <Title>

Status: Proposed | Accepted | Superseded by ADR-YYYY
Date: <YYYY-MM-DD>

## Context
What problem or question prompted this decision?

## Decision
What was decided.

## Alternatives Considered
What else was considered, and why it wasn't chosen.

## Consequences
What this makes easier, harder, or what it commits us to.
```
