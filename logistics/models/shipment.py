from django.db import models

from logistics.models.base import BaseModel
from logistics.models.order import Order
from logistics.models.bulk import BulkBatch


class ShipmentStatus(models.TextChoices):
    CREATED = 'CREATED', 'Created'
    MANIFESTED = 'MANIFESTED', 'Manifested'
    BOOKED = 'BOOKED', 'Booked'
    PICKED_UP = 'PICKED_UP', 'Picked up'
    PICKED_DONE = 'PICKED_DONE', 'Picked done'
    IN_TRANSIT = 'IN_TRANSIT', 'In transit'
    TRANSIT = 'TRANSIT', 'Transit'
    OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', 'Out for delivery'
    DELIVERED = 'DELIVERED', 'Delivered'
    CANCELLED = 'CANCELLED', 'Cancelled'
    FAILED = 'FAILED', 'Failed'


class Shipment(BaseModel):
    order = models.OneToOneField(
        'logistics.Order',
        on_delete=models.PROTECT,
        related_name='shipment',
    )
    courier = models.ForeignKey(
        'logistics.CourierPartner',
        on_delete=models.PROTECT,
        related_name='shipments',
    )
    courier_order_id = models.CharField(max_length=128, blank=True)
    awb_number = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=32, choices=ShipmentStatus.choices, default=ShipmentStatus.CREATED)
    courier_request_payload = models.JSONField(default=dict)
    courier_response_payload = models.JSONField(default=dict)
    failure_payload = models.JSONField(default=dict, blank=True)
    shipping_label = models.TextField(blank=True)
    pickup_address = models.JSONField(default=dict)
    drop_address = models.JSONField(default=dict)
    parcels = models.JSONField(default=list)
    payment_method = models.CharField(max_length=32, choices=Order.PaymentMode.choices, default=Order.PaymentMode.PREPAID)
    cod_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metadata = models.JSONField(default=dict)
    bulk_batch = models.ForeignKey(BulkBatch, on_delete=models.SET_NULL, related_name='shipments', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order.order_number} ({self.courier.code})'
