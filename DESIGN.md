# Design

## Architecture

The API exposes one courier-agnostic contract to internal clients:

- `POST /api/v1/orders/`
- `GET /api/v1/orders/{order_id}/track/`
- `POST /api/v1/orders/{order_id}/cancel/`
- `POST /api/v1/orders/bulk/`

DRF views only validate input, authenticate users, and call services. Business rules live in `logistics/services`. Courier-specific code lives behind the adapter interface in `logistics/couriers`.

The current registered courier is `urbanebolt`. The adapter maps the internal normalized order schema to UrbaneBolt's UAT manifest, tracking, cancel, and token APIs.

## Pattern

The courier layer uses the Adapter plus Registry pattern. Each partner implements the same methods: create, track, and cancel. The registry resolves an adapter by `courier_partner`, which keeps routes, serializers, and services unchanged when another courier is added.

## Database Schema

`Shipment`

- Owner/user
- Internal `order_id`
- Courier partner
- Courier shipment id
- AWB number
- Current status
- Normalized payload
- Courier request and response payloads
- Failure payload
- Timestamps

`TrackingEvent`

- Append-only event history
- Shipment foreign key
- Status, message, location
- Raw courier payload
- Occurrence timestamp

`BulkBatch`

- Owner/user
- Batch UUID
- Status and counts
- Timestamps

`BulkOrderResult`

- Per-order success/failure in a batch
- Error code/message
- Linked order when available

## Bulk Processing Trade-Off

`POST /api/v1/orders/bulk/` returns `202 Accepted` immediately with a `batch_id`. A background thread processes orders using a thread pool. This keeps the HTTP request responsive and supports partial success. For production, the same service boundary can move to Celery/RQ/SQS without changing the public API.

## Auth And Authorization

Signup and login return JWT access and refresh tokens. Shipment endpoints require `Authorization: Bearer <access_token>`. Orders and batches are scoped by user, so one user cannot access another user's shipments or batch results.

## Error Handling

The project uses one normalized error shape with code, message, and details. Unknown couriers return the supported courier list. Courier failures are translated to internal error codes instead of leaking raw partner errors to API consumers.
