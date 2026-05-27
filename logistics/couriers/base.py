from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CourierCreateResponse:
    courier_order_id: str
    awb_number: str
    status: str
    courier_request_payload: Dict[str, Any]
    courier_response_payload: Dict[str, Any]
    failure_response: Dict[str, Any]
    shipping_label: str
    message: str


@dataclass
class CourierTrackingEvent:
    status: str
    message: str = ''
    location: str = ''
    raw_payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CourierTrackResponse:
    status: str
    events: List[CourierTrackingEvent]
    raw_payload: Dict[str, Any]


@dataclass
class CourierCancelResponse:
    status: str
    raw_payload: Dict[str, Any]


class CourierAdapter:
    code = None
    display_name = None

    def create_order(self, shipment):
        raise NotImplementedError

    def create_orders(self, shipments):
        """
        Optional bulk create. Default implementation falls back to per-shipment create.
        Courier adapters can override to call a bulk endpoint.
        """
        results = {}
        for shipment in shipments:
            results[shipment.order.order_number] = self.create_order(shipment)
        return results

    def track_order(self, shipment):
        raise NotImplementedError

    def cancel_order(self, shipment):
        raise NotImplementedError
