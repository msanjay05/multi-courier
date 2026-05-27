import logging

from celery import shared_task

from logistics.couriers.exceptions import CourierError, CourierTemporaryError
from logistics.models import BulkBatch, BulkOrderResult, Order, Shipment, ShipmentStatus
from logistics.services.couriers import get_adapter_or_raise, resolve_courier_partner
from logistics.services.exceptions import UnknownCourierError
from logistics.services.shipments import calculate_parcels

logger = logging.getLogger(__name__)


def update_bacth_status(batch, status, succeeded, failed, user):
    batch.status = status
    batch.succeeded = succeeded
    batch.failed = failed
    batch.updated_by = user
    batch.save()


def creare_bulk_order_result(batch, user, code, message, request_payload, response_payload,internal_order_id=None,courier=None):
    BulkOrderResult.objects.create(
        batch=batch,
        created_by=user,
        internal_order_id=internal_order_id,
        updated_by=user,
        courier=courier,
        success=False,
        error_code=code,
        error_message=message,
        request_payload=request_payload,
        response_payload=response_payload
    )


def create_shipment(user, order, courier_partner, bulk_batch):
    parcels = calculate_parcels(order)
    shipment = Shipment.objects.create(
        created_by=user,
        updated_by=user,
        order=order,
        courier=courier_partner,
        status=ShipmentStatus.CREATED,
        pickup_address=order.warehouse.address.as_dict() if order.warehouse_id else order.shipping_address.as_dict(),
        drop_address=order.shipping_address.as_dict(),
        parcels=parcels,
        payment_method=order.payment_mode,
        cod_amount=order.cod_amount,
        metadata=order.metadata,
        bulk_batch=bulk_batch,
    )
    return shipment


@shared_task(bind=True, autoretry_for=(CourierTemporaryError,), retry_backoff=True, retry_jitter=True, max_retries=3)
def process_bulk_batch(self, batch_id, user_id, orders):
    """
    Background bulk processor.

    - Filters out invalid orders (missing Order, unknown courier)
    - Groups orders by courier_partner
    - Calls courier adapter create_orders() in bulk per partner
    - Updates shipments + creates BulkOrderResult rows
    """
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.get(id=user_id)
    batch = BulkBatch.objects.get(batch_id=batch_id, status=BulkBatch.Status.PENDING)
    batch.status = BulkBatch.Status.PROCESSING
    batch.updated_by = user
    batch.save(update_fields=['status', 'updated_by', 'updated_at'])

    succeeded = 0
    failed = 0

    # Preload Order objects for filtering
    order_numbers = [o.get('order_id') for o in orders if isinstance(o, dict)]
    order_qs = Order.objects.select_related('shipping_address', 'warehouse__address').filter(order_number__in=order_numbers)
    orders_by_number = {o.order_number: o for o in order_qs}

    # Group by courier partner code
    grouped = {}
    for row in orders:
        order_id = (row or {}).get('order_id')
        courier_code = (row or {}).get('courier_partner')

        if not order_id or not courier_code:
            failed += 1
            _result_failure(batch, user, order_id=order_id, code='INVALID_INPUT', message='order_id and courier_partner are required.', payload=row)
            continue

        order = orders_by_number.get(order_id)
        if not order:
            failed += 1
            _result_failure(batch, user, order_id=order_id, code='ORDER_NOT_FOUND', message='Order not found.', payload=row)
            continue

        grouped.setdefault(courier_code, []).append(order)

    # Process each courier group with bulk call
    for courier_code, order_list in grouped.items():
        try:
            courier_partner = resolve_courier_partner(courier_code)
            adapter = get_adapter_or_raise(courier_partner)
        except UnknownCourierError as exc:
            failed +=len(order_list)
            order_numbers=[order.order_number for order in order_list]
            creare_bulk_order_result(batch, user, courier=None, code=exc.code, message=exc.message, request_payload={"order_list":order_numbers,"courier_code":courier_code},response_payload={},internal_order_id=None)
            continue

        # Create shipments (idempotent: if exists, return existing)
        shipments = []
        for order in order_list:
            existing = Shipment.objects.filter(order=order).select_related('courier', 'order').first()
            if existing:
                # If previously failed, treat as failure in bulk result.
                if existing.status != ShipmentStatus.FAILED:
                    failed += 1
                    creare_bulk_order_result(batch, user, code='SHIPMENT_FAILED', message='Shipment already exists', request_payload={},response_payload={},courier=courier_partner,internal_order_id=order.order_number)
                else:
                    existing.bulk_batch = batch
                    existing.save(update_fields=['bulk_batch', 'updated_by', 'updated_at'])
                    succeeded += 1
                    shipments.append(existing)
                continue

            try:
                shipments.append(create_shipment(user, order, courier_partner, batch))
            except Exception as exc:
                failed += 1
                logger.exception('Failed to build shipment', extra={'order_id': order.order_number, 'courier_partner': courier_code})
                creare_bulk_order_result(batch, user, order_id=order.order_number, code='SHIPMENT_BUILD_FAILED', message=str(exc), payload={},internal_order_id=order.order_number,courier=courier_partner)

        if not shipments:
            continue

        try:
            responses_by_order,request_payload,response_payload = adapter.create_orders(shipments)
        except CourierError as exc:
            # Mark all shipments in this courier group as failed
            for shipment in shipments:
                shipment.status = ShipmentStatus.FAILED
                shipment.failure_payload = {'code': exc.code, 'message': exc.message, 'raw_payload': exc.raw_payload}
                shipment.apply_audit_user(user)
                shipment.save(update_fields=['status', 'failure_payload', 'updated_by', 'updated_at'])
                failed += 1
                creare_bulk_order_result(batch, user, order_id=shipment.order.order_number, courier=shipment.courier, code=exc.code, message=exc.message, payload=exc.raw_payload)
            continue

        # Apply per-order responses
        for shipment in shipments:
            resp = responses_by_order.get(shipment.order.order_number,None)
            if not resp:
                shipment.status = ShipmentStatus.FAILED
                shipment.failure_payload = {'code': 'MISSING_COURIER_RESPONSE', 'message': 'Courier response missing for order.'}
                shipment.apply_audit_user(user)
                shipment.save(update_fields=['status', 'failure_payload', 'updated_by', 'updated_at'])
                failed += 1
                creare_bulk_order_result(batch, user, order_id=shipment.order.order_number, courier=shipment.courier, code='MISSING_COURIER_RESPONSE', message='Courier response missing for order.', request_payload={},response_payload={})
                continue

            shipment.courier_order_id = resp.courier_order_id or ''
            shipment.awb_number = resp.awb_number or ''
            shipment.courier_request_payload = resp.courier_request_payload or {}
            shipment.courier_response_payload = resp.courier_response_payload or {}
            shipment.shipping_label = getattr(resp, 'shipping_label', '') or ''
            shipment.failure_payload = getattr(resp, 'failure_response', {}) or {}

            # Normalize status
            raw_status = str(resp.status or '').strip().upper()
            shipment.status = ShipmentStatus.FAILED if raw_status == 'FAILED' else ShipmentStatus.CREATED

            shipment.apply_audit_user(user)
            shipment.bulk_batch = batch
            shipment.save()

            if shipment.status == ShipmentStatus.FAILED:
                failed += 1
            else:
                succeeded += 1

    update_bacth_status(batch, status=BulkBatch.Status.COMPLETED, succeeded=succeeded, failed=failed, user=user)

