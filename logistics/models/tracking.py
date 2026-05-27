from django.db import models

from logistics.models.base import BaseModel
from logistics.models.shipment import Shipment, ShipmentStatus


class TrackingEvent(BaseModel):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_events')
    status = models.CharField(max_length=32, choices=ShipmentStatus.choices)
    message = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    raw_payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField()

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.shipment.order.order_number}: {self.status}'
