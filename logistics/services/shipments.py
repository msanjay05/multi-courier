import json
import logging
import time

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from logistics.couriers.exceptions import CourierAuthError, CourierError, CourierTemporaryError
from logistics.models import Order, Shipment, ShipmentStatus, TrackingEvent
from logistics.services.couriers import get_adapter_or_raise, resolve_courier_partner
from logistics.services.exceptions import (
    LogisticsError,
    ShipmentAccessError,
    ShipmentAlreadyCancelledError,
    ShipmentFailedError,
)

logger = logging.getLogger(__name__)


def get_shipment_or_raise(order_id):
    try:
        return (
            Shipment.objects.select_related('courier', 'order')
            .prefetch_related('tracking_events')
            .get(order__order_number=order_id)
        )
    except Shipment.DoesNotExist as exc:
        raise ShipmentAccessError('Shipment not found.') from exc

def _address_as_dict(address, field_name):
    if address is None:
        raise LogisticsError(f'Order is missing {field_name}.')
    return address.as_dict()


def _map_create_shipment_status(raw_status):
    normalized = str(raw_status or '').strip().upper()
    if normalized == ShipmentStatus.FAILED:
        return ShipmentStatus.FAILED
    return ShipmentStatus.CREATED



def calculate_parcels(order):
    parcels = [
        {
        "weight_kg": "1.20",
        "length_cm": "20.00",
        "width_cm": "15.00",
        "height_cm": "8.00",
        "description": "Books",
        "declared_value": "500.00"
        }
    ]
    return parcels

def create_shipment(user, order,courier_partner):
    adapter = get_adapter_or_raise(courier_partner)
    existing = Shipment.objects.filter(order=order).select_related('courier', 'order').first()
    if existing:
        return existing, True
    
    parcels=calculate_parcels(order)

    shipment = Shipment(
        created_by=user,
        updated_by=user,
        order=order,
        courier=courier_partner,
        status=ShipmentStatus.CREATED,
        pickup_address=_address_as_dict(order.warehouse.address if order.warehouse_id else order.shipping_address, 'pickup address'),
        drop_address=_address_as_dict(order.shipping_address, 'shipping_address'),
        parcels=parcels,
        payment_method=order.payment_mode,
        cod_amount=order.cod_amount,
        metadata=order.metadata,
    )
    shipment.save()

    try:
        courier_response = _call_with_retries(adapter.create_order,shipment)
    except CourierError as exc:
        _mark_shipment_failed(shipment, user, exc)
        logger.exception(
            'Courier create failed',
            extra={
                'order_id': order.order_number,
                'courier_partner': courier_partner.code,
                'error_type': exc.code,
            },
        )
        if isinstance(exc, CourierTemporaryError):
            raise
        raise ShipmentFailedError(
            exc.message,
            details={
                'order_id': order.order_number,
                'shipment_status': shipment.status,
                'failure_payload': shipment.failure_payload,
            },
        ) from exc

    shipment.courier_order_id = courier_response.courier_order_id
    shipment.awb_number = courier_response.awb_number
    shipment.status = _map_create_shipment_status(courier_response.status)
    shipment.courier_request_payload = courier_response.courier_request_payload or {}
    shipment.courier_response_payload = courier_response.courier_response_payload or {}
    shipment.shipping_label = courier_response.shipping_label
    shipment.failure_payload = courier_response.failure_response or {}
    shipment.apply_audit_user(user)
    shipment.save()
    message = courier_response.message or 'Shipment created'

    _create_tracking_event(shipment, user, shipment.status, 'Shipment created', courier_response.courier_response_payload)
    return shipment, message


def track_shipment(user, order_id):
    shipment = get_shipment_or_raise(order_id)
    adapter = get_adapter_or_raise(shipment.courier)
    response = _call_with_retries(adapter.track_order, shipment)
    shipment.status = response.status
    shipment.courier_response_payload = response.raw_payload
    shipment.apply_audit_user(user)
    shipment.save()
    now = timezone.now()
    for event in response.events:
        _create_tracking_event(
            shipment,
            user,
            event.status,
            event.message,
            event.raw_payload,
            location=event.location,
            occurred_at=now,
        )
    return shipment


def cancel_shipment(user, order_id):
    shipment = get_shipment_or_raise(order_id)
    if shipment.status == ShipmentStatus.CANCELLED:
        raise ShipmentAlreadyCancelledError('Shipment cancellation is not allowed because it is already cancelled.')
    adapter = get_adapter_or_raise(shipment.courier)
    response = _call_with_retries(adapter.cancel_order, shipment)
    shipment.status = response.status
    shipment.courier_response_payload = response.raw_payload
    shipment.apply_audit_user(user)
    shipment.save()
    _create_tracking_event(
        shipment,
        user,
        response.status,
        'Shipment cancelled',
        response.raw_payload,
    )
    return shipment


def _create_tracking_event(shipment, user, status, message, raw_payload, *, location='', occurred_at=None):
    # Webhooks may be unauthenticated; created_by/updated_by are nullable FKs.
    audit_user = user if user and getattr(user, 'is_authenticated', False) else None
    TrackingEvent.objects.create(
        shipment=shipment,
        created_by=audit_user,
        updated_by=audit_user,
        status=status,
        message=message,
        location=location,
        raw_payload=raw_payload or {},
        occurred_at=occurred_at or timezone.now(),
    )


def _map_status(value):
    """
    Normalize external courier status strings into internal `ShipmentStatus` values.
    """
    normalized = str(value or '').strip().upper().replace(' ', '_')
    status_map = {
        'CREATED': ShipmentStatus.CREATED,
        'MANIFESTED': ShipmentStatus.MANIFESTED,
        'BOOKED': ShipmentStatus.BOOKED,
        'PICKED_UP': ShipmentStatus.PICKED_UP,
        'PICKUP_DONE': ShipmentStatus.PICKED_DONE,
        'IN_TRANSIT': ShipmentStatus.IN_TRANSIT,    
        'TRANSIT': ShipmentStatus.TRANSIT,
        'OUT_FOR_DELIVERY': ShipmentStatus.OUT_FOR_DELIVERY,
        'DELIVERED': ShipmentStatus.DELIVERED,
        'CANCELLED': ShipmentStatus.CANCELLED,
        'CANCELED': ShipmentStatus.CANCELLED,
        'FAILED': ShipmentStatus.FAILED,
    }
    return status_map.get(normalized, ShipmentStatus.IN_TRANSIT if normalized else ShipmentStatus.CREATED)


def apply_webhook_status_update(
    *,
    user,
    order_id=None,
    awb_number=None,
    status,
    message='',
    location='',
    raw_payload=None,
    occurred_at=None,
):
    if not order_id and not awb_number:
        raise LogisticsError('Webhook must include `order_id` or `awb_number`.')

    if order_id:
        shipment = get_shipment_or_raise(order_id)
    else:
        try:
            shipment = (
                Shipment.objects.select_related('courier', 'order')
                .prefetch_related('tracking_events')
                .get(awb_number=awb_number)
            )
        except Shipment.DoesNotExist as exc:
            raise ShipmentAccessError('Shipment not found.') from exc

    normalized_status = _map_status(status)

    # Idempotency: if status hasn't changed, do not create duplicate tracking rows.
    if shipment.status == normalized_status:
        return shipment

    latest_event = (
        shipment.tracking_events.all().order_by('-occurred_at', '-created_at').first()
        if hasattr(shipment, 'tracking_events')
        else TrackingEvent.objects.filter(shipment=shipment).order_by('-occurred_at', '-created_at').first()
    )
    if latest_event and latest_event.status == normalized_status:
        return shipment

    shipment.status = normalized_status
    if raw_payload is not None:
        shipment.courier_response_payload = raw_payload
    if user and getattr(user, 'is_authenticated', False):
        shipment.apply_audit_user(user)
    shipment.save()

    _create_tracking_event(
        shipment=shipment,
        user=user,
        status=normalized_status,
        message=message or '',
        raw_payload=raw_payload or {},
        location=location or '',
        occurred_at=occurred_at,
    )
    return shipment


def _call_with_retries(func, *args):
    attempts = settings.COURIER_RETRY_COUNT + 1
    last_error = None
    for attempt in range(attempts):
        try:
            return func(*args)
        except CourierAuthError:
            if attempt == 0:
                continue
            raise
        except CourierTemporaryError as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(settings.COURIER_RETRY_BACKOFF_SECONDS * (2 ** attempt))
                continue
            raise
    if last_error:
        raise last_error


def _mark_shipment_failed(shipment, user, exc):
    shipment.status = ShipmentStatus.FAILED
    shipment.failure_payload = {
        'code': exc.code,
        'message': exc.message,
        'raw_payload': exc.raw_payload,
    }
    shipment.apply_audit_user(user)
    shipment.save()
    _create_tracking_event(
        shipment,
        user,
        ShipmentStatus.FAILED,
        exc.message,
        shipment.failure_payload,
    )


def _make_json_safe(value):
    return json.loads(json.dumps(value, cls=DjangoJSONEncoder))
