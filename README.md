# Multi Courier

Django REST Framework backend for a courier-agnostic shipment API with:
- Order + order-item creation
- Shipment creation/tracking/cancel
- Bulk shipment creation via Celery background jobs
- Webhook-based tracking updates

Supported couriers:
- `urbanebolt` (UAT)
- `mock` (local dev/testing, no external HTTP)

## Setup

```bash
git clone git@github.com:msanjay05/multi-courier.git
cd multi-courier
python -m venv venv
sourve venv active
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Edit `.env` with your local values (UrbaneBolt credentials, secret key, etc.). `.env` is gitignored.

### Example `.env`

```env
# Django
DJANGO_SECRET_KEY=local-dev-secret-change-in-production
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Celery / Redis (bulk shipments)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Webhook (optional)
COURIER_WEBHOOK_SECRET=

# Default warehouse (optional)
DEFAULT_WAREHOUSE_CODE=DEFAULT

# UrbaneBolt (optional if you use courier_partner=\"mock\")
URBANEBOLT_BASE_URL=https://uat.urbanebolt.in
URBANEBOLT_USERNAME=
URBANEBOLT_PASSWORD=
URBANEBOLT_CUSTOMER_CODE=
URBANEBOLT_SERVICE_TYPE=SDD
```

## Run commands

### Start the Django API

```bash
cd multi-courier
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py runserver
```

### Start Redis + Celery worker (required for bulk shipments)

```bash
# terminal 1
redis-server

# terminal 2 (from repo root)
celery -A multi_courier worker -l info
```

### Run Celery tasks inline (optional dev mode)

If you don’t want Redis/Celery locally, you can run tasks eagerly:

```bash
export CELERY_TASK_ALWAYS_EAGER=true
../.venv/bin/python manage.py runserver
```

### Celery (bulk shipments)

Bulk shipment processing runs in Celery. By default it uses Redis:

```bash
redis-server
celery -A multi_courier worker -l info
```

## Environment Variables

All variables are loaded from `.env` via `python-dotenv`.

## Auth

All APIs (except webhook) require:

```http
Authorization: Bearer <access_token>
```

Create an account:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","email":"demo@example.com","password":"strong-pass-123"}'
```

Login:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"strong-pass-123"}'
```

## APIs

### Create Order (creates `Order` + `OrderItem`)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/order/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_mode": "PREPAID",
    "shipping_address": {
      "name": "Customer",
      "phone": "8888888888",
      "line1": "Park Street",
      "city": "Kolkata",
      "state": "WB",
      "postal_code": "700016",
      "country": "IN"
    },
    "items": [
      { "sku": "BOOK-001", "name": "Books", "quantity": 1, "unit_price": "1000.00" }
    ]
  }'
```

The API generates a unique `order_number` and returns it as `order_id`.

### Create Shipment

Create a shipment for an existing order:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/shipment/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD-1001",
    "courier_partner": "urbanebolt"
  }'
```

You can also use `courier_partner: "mock"` for local testing.

### Track Shipment (read-only)

This endpoint does not call courier tracking. It returns tracking history from the `TrackingEvent` table.

```bash
curl -H "Authorization: Bearer <access_token>" \
  http://127.0.0.1:8000/api/v1/shipment/ORD-1001/track/
```

### Cancel Shipment

Cancellation is rejected if the shipment is already cancelled.

```bash
curl -X POST -H "Authorization: Bearer <access_token>" \
  http://127.0.0.1:8000/api/v1/shipment/ORD-1001/cancel/
```

### Bulk Create Shipments (Celery background)

Bulk create (up to 100 orders) enqueues a background job. Poll status with the batch id.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/shipment/bulk/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"orders":[{"order_id":"ORD-2001","courier_partner":"urbanebolt"},{"order_id":"ORD-2002","courier_partner":"mock"}]}'
```

Check bulk status:

```bash
curl -H "Authorization: Bearer <access_token>" \
  http://127.0.0.1:8000/api/v1/shipment/bulk/<batch_id>/
```

### Webhook (creates tracking)

Webhook receives status updates and appends a `TrackingEvent`. Optional secret header:

```http
X-Webhook-Secret: <COURIER_WEBHOOK_SECRET>
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/shipment/webhook/ \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: <optional>" \
  -d '{
    "order_id": "ORD-1001",
    "status": "DELIVERED",
    "message": "Delivered",
    "location": "Kolkata",
    "raw_payload": {"source":"curl"}
  }'
```

## Error Shape

All endpoint errors use:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable summary.",
    "details": {}
  }
}
```

## How To Add A Courier

1. Create `logistics/couriers/<partner>.py`.
2. Implement `CourierAdapter.create_order`, `create_orders` (optional), `track_order`, and `cancel_order`.
3. Register it in `logistics/couriers/registry.py`.
4. Add environment variables for credentials/base URL/timeouts.

Routes, serializers, and order services do not need changes for a new courier.

## Tests

```bash
../.venv/bin/python manage.py test
```
