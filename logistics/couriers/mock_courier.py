from datetime import datetime, timezone

from logistics.couriers.base import (
    CourierAdapter,
    CourierCancelResponse,
    CourierCreateResponse,
    CourierTrackingEvent,
    CourierTrackResponse,
)
from logistics.models import ShipmentStatus


class MockCourierAdapter(CourierAdapter):
    """
    Very small fake courier adapter for local dev/testing.

    Rules:
    - Always succeeds unless `shipment.metadata.get("force_fail")` is true.
    - Bulk create uses the same rules per shipment.
    - Track returns a single event with the current shipment status.
    """

    code = 'mock'
    display_name = 'MockCourier'

    def _should_fail(self, shipment):
        metadata = shipment.metadata or {}
        return bool(metadata.get('force_fail'))

    def _awb_for(self, shipment):
        # Stable fake AWB: MOCK-<order_number>
        return f'MOCK-{shipment.order.order_number}'

    def create_order(self, shipment):
        if self._should_fail(shipment):
            return CourierCreateResponse(
                courier_order_id='',
                awb_number='',
                status='FAILED',
                courier_request_payload={'mock': True, 'order_id': shipment.order.order_number},
                courier_response_payload={'mock': True, 'ok': False},
                failure_response={'message': 'Forced failure (mock courier).'},
                shipping_label='',
                message='Forced failure (mock courier).',
            )

        return CourierCreateResponse(
            courier_order_id=shipment.order.order_number,
            awb_number=self._awb_for(shipment),
            status='SUCCESS',
            courier_request_payload={'mock': True, 'order_id': shipment.order.order_number},
            courier_response_payload={'mock': True, 'ok': True},
            failure_response={},
            shipping_label=f'LABEL-{shipment.order.order_number}',
            message='Mock shipment created.',
        )

    def create_orders(self, shipments):
        by_order = {}
        request_payload = [{'mock': True, 'order_id': s.order.order_number} for s in shipments]
        response_payload = {'mock': True, 'count': len(shipments)}
        for s in shipments:
            by_order[s.order.order_number] = self.create_order(s)
        return by_order, request_payload, response_payload

    def track_order(self, shipment):
        now = datetime.now(timezone.utc)
        return CourierTrackResponse(
            status=shipment.status or ShipmentStatus.CREATED,
            events=[
                CourierTrackingEvent(
                    status=shipment.status or ShipmentStatus.CREATED,
                    message='Mock tracking event.',
                    location='',
                    raw_payload={'mock': True, 'awb': shipment.awb_number},
                )
            ],
            raw_payload={'mock': True, 'checked_at': now.isoformat()},
        )

    def cancel_order(self, shipment):
        return CourierCancelResponse(status=ShipmentStatus.CANCELLED, raw_payload={'mock': True, 'ok': True})

