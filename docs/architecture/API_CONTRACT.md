# Atlas — API Contract (v1, proposed)

Status: Accepted (v1)
Related: [Architecture](./ARCHITECTURE.md)

This defines the initial REST contract between the frontend and backend. It
is intentionally minimal — only what's needed to support the product brief's
scope. Endpoints are versioned under `/api/v1`. All request/response bodies
are JSON except the CSV import upload.

This is a contract for the engineering team to build against, not a final
OpenAPI spec. The backend implementation should generate/publish an OpenAPI
schema (a natural byproduct of FastAPI) as the source of truth once built;
this document should stay in sync with it.

## Conventions

- Content type: `application/json` unless noted.
- Dates: ISO-8601 (`YYYY-MM-DD`).
- Monetary values: numbers, single assumed currency (see Open Question in
  ARCHITECTURE.md — this will need revisiting if multi-currency is added).
- Errors: `{ "error": { "code": "string", "message": "string", "details": ... } }`
  with a matching 4xx/5xx HTTP status.
- IDs: opaque strings (implementation may use integers or UUIDs).

## Assets

### `GET /api/v1/assets`
List all registered assets.

Response `200`:
```json
[
  { "id": "1", "symbol": "PETR4", "name": "Petrobras PN", "asset_type": "stock" }
]
```

### `POST /api/v1/assets`
Register a new asset.

Request:
```json
{ "symbol": "PETR4", "name": "Petrobras PN", "asset_type": "stock" }
```
Response `201`: the created asset, as above.
Response `409`: asset with the same identity already exists (see Open
Question on asset identity in ARCHITECTURE.md).

### `GET /api/v1/assets/{asset_id}`
Fetch a single asset. `404` if not found.

## Transactions

### `GET /api/v1/transactions`
List recorded transactions, most recent first. Supports optional
`?asset_id=` filter.

Response `200`:
```json
[
  {
    "id": "10",
    "asset_id": "1",
    "type": "buy",
    "quantity": 100,
    "unit_price": 32.50,
    "fees": 4.90,
    "date": "2026-03-10"
  }
]
```

### `POST /api/v1/transactions`
Record a buy or sell transaction.

Request:
```json
{
  "asset_id": "1",
  "type": "buy",
  "quantity": 100,
  "unit_price": 32.50,
  "fees": 4.90,
  "date": "2026-03-10"
}
```
Response `201`: the created transaction.
Response `422`: invalid payload. This includes, but is not limited to:
- negative or zero quantity/unit price;
- a `sell` for a quantity greater than the asset's currently held quantity
  (rejected per [ADR-0004](./decisions/0004-cost-basis-method.md) — no short
  positions in v1), e.g.:
```json
{
  "error": {
    "code": "insufficient_position",
    "message": "Cannot sell 50 units of PETR4: only 30 are held.",
    "details": { "asset_id": "1", "requested": 50, "held": 30 }
  }
}
```
This rule is enforced by the domain layer, not just as an input-shape check,
since it is a business invariant (see ADR-0004).

### `GET /api/v1/transactions/{transaction_id}`
Fetch a single transaction. `404` if not found.

### `POST /api/v1/transactions/import`
Import transactions from a CSV file.

Request: `multipart/form-data` with a `file` field.

Proposed generic Atlas CSV schema for v1 (columns, header row required):
```
symbol,type,quantity,unit_price,fees,date
PETR4,buy,100,32.50,4.90,2026-03-10
```

Response `200`:
```json
{
  "imported": 12,
  "skipped": 1,
  "errors": [
    { "row": 5, "message": "unknown asset symbol XYZ4" }
  ]
}
```

Broker-specific CSV formats are explicitly out of scope for v1 (see Open
Questions in ARCHITECTURE.md); this generic schema is the interim contract.

## Portfolio

### `GET /api/v1/portfolio/positions`
Current positions, derived from transaction history.

Response `200`:
```json
[
  {
    "asset_id": "1",
    "symbol": "PETR4",
    "quantity": 100,
    "average_price": 32.50,
    "current_price": null,
    "market_value": null,
    "unrealized_pnl": null
  }
]
```
`average_price` is the moving weighted-average cost as of now (see
[ADR-0004](./decisions/0004-cost-basis-method.md)). `current_price`,
`market_value`, and `unrealized_pnl` are `null` until the market price
source (Open Question in ARCHITECTURE.md) is decided and implemented; the
field shape is defined now so the frontend can build against it.

### `GET /api/v1/portfolio/summary`
Response `200`:
```json
{
  "total_market_value": null,
  "total_realized_pnl": 0,
  "total_unrealized_pnl": null
}
```
`total_realized_pnl` is computed under moving weighted-average cost (ADR-0004).

### `GET /api/v1/portfolio/allocation`
Allocation breakdown for visualization.

Response `200`:
```json
[
  { "asset_id": "1", "symbol": "PETR4", "weight": 1.0 }
]
```
`weight` requires market value per asset; behavior when prices are
unavailable (e.g. weight by cost basis instead) is an implementation detail
to resolve alongside the market price open question.

## Not Yet Specified (deferred, not blocking v1 start)

- Editing/deleting assets and transactions (brief doesn't request this;
  add only if required).
- Pagination for list endpoints (fine to defer given single-user local
  scale; revisit if transaction volume grows).
- Authentication headers (none in v1, per product brief).
