# Multi Courier

Django REST Framework backend for a courier-agnostic shipment API with UrbaneBolt UAT integrated as the active courier adapter.

## Setup

```bash
cd /Users/sanjaykumar/Documents/Codex/2026-05-26/create-a-django-project-with-multi/multi-courier
cp .env.example .env
../.venv/bin/python -m pip install -r requirements.txt
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py runserver
```

Edit `.env` with your local values (UrbaneBolt credentials, secret key, etc.). `.env` is gitignored; `.env.example` is the committed template.

## Environment Variables

All variables are loaded from `.env` via `python-dotenv`. See `.env.example` for the full list.

## Auth

All shipment APIs require:

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

## Order APIs

Create a shipment:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD-1001",
    "courier_partner": "urbanebolt",
    "pickup_address": {
      "name": "Warehouse",
      "phone": "9999999999",
      "line1": "MG Road",
      "city": "Bengaluru",
      "state": "KA",
      "postal_code": "560001",
      "country": "IN"
    },
    "drop_address": {
      "name": "Customer",
      "phone": "8888888888",
      "line1": "Park Street",
      "city": "Kolkata",
      "state": "WB",
      "postal_code": "700016",
      "country": "IN"
    },
    "parcels": [
      {"weight_kg": "1.20", "description": "Books", "declared_value": "500.00"}
    ],
    "payment_method": "PREPAID"
  }'
```

Track:

```bash
curl -H "Authorization: Bearer <access_token>" \
  http://127.0.0.1:8000/api/v1/orders/ORD-1001/track/
```

Cancel:

```bash
curl -X POST -H "Authorization: Bearer <access_token>" \
  http://127.0.0.1:8000/api/v1/orders/ORD-1001/cancel/
```

Bulk create, up to 100 orders:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/bulk/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"orders":[{"order_id":"ORD-2001","courier_partner":"urbanebolt","pickup_address":{"name":"Warehouse","phone":"9999999999","line1":"MG Road","city":"Bengaluru","state":"KA","postal_code":"560001","country":"IN"},"drop_address":{"name":"Customer","phone":"8888888888","line1":"Park Street","city":"Kolkata","state":"WB","postal_code":"700016","country":"IN"},"parcels":[{"weight_kg":"1.20","description":"Books","declared_value":"500.00"}],"payment_method":"PREPAID"}]}'
```

Check bulk status:

```bash
curl -H "Authorization: Bearer <access_token>" \
  http://127.0.0.1:8000/api/v1/orders/bulk/<batch_id>/
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
2. Implement `CourierAdapter.create_order`, `track_order`, and `cancel_order`.
3. Register it in `logistics/couriers/registry.py`.
4. Add environment variables for credentials/base URL/timeouts.

Routes, serializers, and order services do not need changes for a new courier.

## Tests

```bash
../.venv/bin/python manage.py test
```
