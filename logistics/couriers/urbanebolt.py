import json
from datetime import date

import requests
from django.conf import settings
from requests import RequestException

from logistics.couriers.base import (
    CourierAdapter,
    CourierCancelResponse,
    CourierCreateResponse,
    CourierTrackingEvent,
    CourierTrackResponse,
)
from logistics.couriers.exceptions import CourierAuthError, CourierTemporaryError, CourierValidationError
from logistics.models import ShipmentStatus


class UrbaneBoltAdapter(CourierAdapter):
    code = 'urbanebolt'
    display_name = 'UrbaneBolt'

    def __init__(self):
        self._token = None

    def create_order(self, shipment):
        manifest_payload = [self._to_manifest_payload(shipment)]
        response = self._request('POST', '/api/v1/services/manifest/', json=manifest_payload, auth=True)
        success_response = response.get('successResponse', [])[0] if isinstance(response.get('successResponse', []), list) and len(response.get('successResponse', [])) > 0 else None
        failure_response = response.get('errorResponse', [])[0] if isinstance(response.get('errorResponse', []), list) and len(response.get('errorResponse', [])) > 0 else None

        message = ''
        if success_response:
            message = success_response.get('message', 'Suceessfully created shipment')
        elif failure_response:
            message = failure_response.get('message', 'Failed to create shipment')

        return CourierCreateResponse(
            courier_order_id=success_response.get('orderNumber', shipment.order.order_number) if success_response else '',
            awb_number=success_response.get('awbNumber', '') if success_response else '',
            status="SUCCESS" if success_response else "FAILED",
            courier_request_payload=manifest_payload,
            courier_response_payload=response,
            failure_response=failure_response,
            shipping_label=success_response.get('shippingLabel', '') if success_response else '',
            message=message,
        )

    def create_orders(self, shipments):
        manifest_payload = [self._to_manifest_payload(s) for s in shipments]
        response = self._request('POST', '/api/v1/services/manifest/', json=manifest_payload, auth=True)

        success_list = response.get('successResponse', []) if isinstance(response.get('successResponse', []), list) else []
        error_list = response.get('errorResponse', []) if isinstance(response.get('errorResponse', []), list) else []

        by_order = {}

        for row in success_list:
            order_number = row.get('orderNumber') or row.get('order_number')
            if not order_number:
                continue
            by_order[str(order_number)] = CourierCreateResponse(
                courier_order_id=row.get('orderNumber', ''),
                awb_number=row.get('awbNumber', ''),
                status='SUCCESS',
                courier_request_payload=manifest_payload,
                courier_response_payload=row,
                failure_response={},
                shipping_label=row.get('shippingLabel', ''),
                message=row.get('message', 'Successfully created shipment'),
            )

        for row in error_list:
            order_number = row.get('orderNumber') or row.get('order_number')
            if not order_number:
                continue
            by_order[str(order_number)] = CourierCreateResponse(
                courier_order_id='',
                awb_number='',
                status='FAILED',
                courier_request_payload=manifest_payload,
                courier_response_payload=row,
                failure_response=row,
                shipping_label='',
                message=row.get('message', 'Failed to create shipment'),
            )

        return by_order,manifest_payload,response

    def track_order(self, shipment):
        response = self._request(
            'GET',
            '/api/v1/services/tracking-pub/',
            params={'awb': shipment.awb_number},
            auth=True,
        )
        events = _extract_tracking_events(response)
        status = events[-1].status if events else _map_status(_pick(response, 'status', 'current_status') or shipment.status)
        return CourierTrackResponse(status=status, events=events, raw_payload=response)

    def cancel_order(self, shipment):
        response = self._request(
            'POST',
            '/api/v1/services/cancel/',
            json={'awbs': shipment.awb_number},
            auth=True,
        )
        return CourierCancelResponse(status=ShipmentStatus.CANCELLED, raw_payload=response)

    def _to_manifest_payload(self, shipment):
        customer_code = settings.URBANEBOLT_CUSTOMER_CODE
        if not customer_code:
            raise CourierValidationError(
                'URBANEBOLT_CUSTOMER_CODE is required to create UrbaneBolt shipments.'
            )

        pickup = shipment.pickup_address
        drop = shipment.drop_address
        parcels = shipment.parcels
        first_parcel = parcels[0]
        metadata = shipment.metadata or {}
        declared_value = sum(float(parcel.get('declared_value') or 0) for parcel in parcels) or 1
        collectable_value = float(shipment.cod_amount) if shipment.payment_method == 'COD' else 0

        return {
            'customerCode': customer_code,
            'orderNumber': shipment.order.order_number,
            'declaredValue': declared_value,
            'itemDescription': first_parcel.get('description') or metadata.get('item_description', 'Shipment'),
            'collectableValue': collectable_value,
            'height': float(first_parcel.get('height_cm') or metadata.get('height_cm') or 1),
            'length': float(first_parcel.get('length_cm') or metadata.get('length_cm') or 1),
            'pieces': len(parcels),
            'weight': sum(float(parcel.get('weight_kg') or 0) for parcel in parcels),
            'breadth': float(first_parcel.get('width_cm') or metadata.get('width_cm') or 1),
            'serviceType': metadata.get('service_type', settings.URBANEBOLT_SERVICE_TYPE),
            'payMode': 'COD' if shipment.payment_method == 'COD' else 'PPD',
            'rtnCity': pickup['city'],
            'rtnName': pickup['name'],
            'consCity': drop['city'],
            'consName': drop['name'],
            'rtnEmail': pickup.get('email', ''),
            'rtnState': pickup['state'],
            'shprCity': pickup['city'],
            'shprName': pickup['name'],
            'consEmail': drop.get('email', ''),
            'consState': drop['state'],
            'rtnMobile': pickup['phone'],
            'shprEmail': pickup.get('email', ''),
            'shprState': pickup['state'],
            'consMobile': drop['phone'],
            'rtnAddress': _address_line(pickup),
            'rtnAddressType': metadata.get('return_address_type', 'Seller'),
            'rtnCountry': _country_name(pickup.get('country')),
            'rtnPincode': _numeric_pincode(pickup['postal_code']),
            'shprMobile': pickup['phone'],
            'consAddress': _address_line(drop),
            'consAddressType': metadata.get('consignee_address_type', 'Home'),
            'consCountry': _country_name(drop.get('country')),
            'consPincode': _numeric_pincode(drop['postal_code']),
            'invoiceNumber': metadata.get('invoice_number', shipment.order.order_number),
            'invoiceDate': metadata.get('invoice_date', date.today().isoformat()),
            'shprAddress': _address_line(pickup),
            'shprAddressType': metadata.get('shipper_address_type', 'Seller'),
            'shprCountry': _country_name(pickup.get('country')),
            'shprPincode': _numeric_pincode(pickup['postal_code']),
            'invoiceValue': float(metadata.get('invoice_value', declared_value)),
            'itemQuantity': int(metadata.get('item_quantity', len(parcels))),
        }

    def _request(self, method, path, *, json=None, params=None, auth=False):
        headers = {'Content-Type': 'application/json'}
        if auth:
            headers['Authorization'] = f'Bearer {self._get_token()}'

        url = f'{settings.URBANEBOLT_BASE_URL.rstrip("/")}{path}'
        try:
            response = requests.request(
                method,
                url,
                json=json,
                params=params,
                headers=headers,
                timeout=settings.COURIER_TIMEOUT_SECONDS,
            )
        except RequestException as exc:
            raise CourierTemporaryError('Could not reach UrbaneBolt.', raw_payload={'reason': str(exc)}) from exc

        raw_payload = _decode_response(response.content)
        if response.status_code in (401, 403):
            self._token = None
            raise CourierAuthError('UrbaneBolt authentication failed.', raw_payload=raw_payload)
        if 500 <= response.status_code < 600:
            raise CourierTemporaryError('UrbaneBolt service is temporarily unavailable.', raw_payload=raw_payload)
        if not response.ok:
            raise CourierValidationError('UrbaneBolt rejected the shipment request.', raw_payload=raw_payload)
        
        return raw_payload

    def _get_token(self):
        if self._token:
            return self._token
        if not settings.URBANEBOLT_USERNAME or not settings.URBANEBOLT_PASSWORD:
            raise CourierValidationError('UrbaneBolt username and password are required.')
        response = self._request(
            'POST',
            '/api/v1/auth/getToken/',
            json={
                'username': settings.URBANEBOLT_USERNAME,
                'password': settings.URBANEBOLT_PASSWORD,
            },
        )
        token = _extract_token(response)
        if not token:
            raise CourierAuthError('UrbaneBolt token response did not include a token.', raw_payload=response)
        self._token = token
        return self._token


def _decode_response(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw.decode('utf-8'))
    except json.JSONDecodeError:
        return {'raw': raw.decode('utf-8', errors='replace')}


def _extract_token(response):
    return _pick(response, 'token', 'access', 'access_token', 'key') or _pick(response.get('data', {}), 'token', 'access')


def _extract_tracking_events(response):
    raw_events = response.get('history') or response.get('events') or response.get('tracking') or response.get('data') or []
    if isinstance(raw_events, dict):
        raw_events = raw_events.get('history') or raw_events.get('events') or [raw_events]
    if not isinstance(raw_events, list):
        raw_events = []
    return [
        CourierTrackingEvent(
            status=_map_status(_pick(event, 'status', 'shipmentStatus', 'current_status')),
            message=str(_pick(event, 'message', 'remarks', 'description') or ''),
            location=str(_pick(event, 'location', 'city') or ''),
            raw_payload=event,
        )
        for event in raw_events
        if isinstance(event, dict)
    ]


def _map_status(value):
    normalized = str(value or '').strip().upper().replace(' ', '_')
    status_map = {
        'CREATED': ShipmentStatus.CREATED,
        'MANIFESTED': ShipmentStatus.MANIFESTED,
        'BOOKED': ShipmentStatus.BOOKED,
        'PICKED_UP': ShipmentStatus.PICKED_UP,
        'PICKUP_DONE': ShipmentStatus.PICKED_UP,
        'IN_TRANSIT': ShipmentStatus.IN_TRANSIT,
        'TRANSIT': ShipmentStatus.IN_TRANSIT,
        'OUT_FOR_DELIVERY': ShipmentStatus.IN_TRANSIT,
        'DELIVERED': ShipmentStatus.DELIVERED,
        'CANCELLED': ShipmentStatus.CANCELLED,
        'CANCELED': ShipmentStatus.CANCELLED,
        'FAILED': ShipmentStatus.FAILED,
    }
    return status_map.get(normalized, ShipmentStatus.IN_TRANSIT if normalized else ShipmentStatus.CREATED)


def _pick(source, *keys):
    if not isinstance(source, dict):
        return None
    for key in keys:
        if key in source and source[key] not in (None, ''):
            return source[key]
    return None


def _address_line(address):
    return ', '.join(part for part in [address.get('line1'), address.get('line2')] if part)


def _country_name(country_code):
    return 'INDIA' if not country_code or country_code.upper() == 'IN' else country_code


def _numeric_pincode(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value
