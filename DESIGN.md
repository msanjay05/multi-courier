# Design

## Architecture

The API exposes courier-agnostic contracts to internal clients:

- **Order**
  - `POST /api/v1/order/` (creates `Order` + nested `OrderItem`)
- **Shipment**
  - `POST /api/v1/shipment/` (creates shipment for an existing `Order`)
  - `GET /api/v1/shipment/{order_id}/track/` (read-only; returns tracking history from DB)
  - `POST /api/v1/shipment/{order_id}/cancel/`
  - `POST /api/v1/shipment/bulk/` (async; Celery background job)
  - `POST /api/v1/shipment/webhook/` (courier webhook; appends tracking)

DRF views only validate input, authenticate users, and call services. Business rules live in `logistics/services`. Courier-specific code lives behind the adapter interface in `logistics/couriers`.

Registered couriers:
- `urbanebolt` (UAT integration)
- `mock` (local dev/testing; no external HTTP)

## Pattern

The courier layer uses the Adapter + Registry pattern. Each partner implements:
- `create_order(shipment)`
- `create_orders(shipments)` (optional bulk create; default falls back to per-shipment)
- `track_order(shipment)`
- `cancel_order(shipment)`

The registry resolves an adapter by `courier_partner`, which keeps routes, serializers, and services unchanged when another courier is added.

## Database Schema

`Order`

- `order_number` (generated server-side; unique)
- payment mode / COD amount / totals
- `shipping_address`, `billing_address` (FKs)
- `warehouse` (FK, default warehouse assigned if not provided)
- metadata + timestamps

`OrderItem`

- FK to `Order`
- sku/name/qty/price/tax + metadata

`Shipment`

- FK to `Order`
- Courier partner (FK to `CourierPartner`)
- Courier shipment/order id
- AWB number
- Current status
- Courier request and response payloads
- Failure payload
- `bulk_batch` (nullable FK to `BulkBatch`)
- Timestamps

`TrackingEvent`

- Append-only event history
- Shipment foreign key
- Status, message, location
- Raw courier payload
- Occurrence timestamp

`BulkBatch`

- Batch UUID
- Status and counts
- `order_list` (raw request list persisted for debugging)
- Timestamps

`BulkOrderResult`

- Per-order success/failure in a batch
- Error code/message
- `request_payload` / `response_payload` JSON for debugging
- Courier partner when resolvable

## Bulk Processing Trade-Off

`POST /api/v1/shipment/bulk/` returns `202 Accepted` immediately with a `batch_id`. A Celery background task processes orders. This keeps the HTTP request responsive and supports partial success. The task:

- filters out invalid orders
- groups by `courier_partner`
- bulk-calls the courier adapter where supported (`create_orders`)
- stores per-order results in `BulkOrderResult`


## Auth And Authorization

Signup and login return JWT access and refresh tokens. Shipment endpoints require `Authorization: Bearer <access_token>`. Orders and batches are scoped by user, so one user cannot access another user's shipments or batch results.

## Error Handling

The project uses one normalized error shape with code, message, and details. Courier failures are translated to internal error codes instead of leaking raw partner errors to API consumers.

Tracking updates are webhook-driven: `GET /track/` is read-only and does not call courier tracking APIs.
