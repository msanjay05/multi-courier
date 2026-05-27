from django.db import models

from logistics.models.base import BaseModel


class ShippingItem(BaseModel):
    shipment = models.ForeignKey('logistics.Shipment', on_delete=models.CASCADE, related_name='shipping_items')
    sku = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    declared_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2)
    length_cm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    width_cm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.shipment.order.order_number} - {self.name}'
