from django.db import models

from logistics.models.base import BaseModel


class OrderItem(BaseModel):
    order = models.ForeignKey('logistics.Order', on_delete=models.CASCADE, related_name='items')
    sku = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hsn_code = models.CharField(max_length=32, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.order.order_number} - {self.sku}'
