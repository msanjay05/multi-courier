from django.db import models

from logistics.models.base import BaseModel


class Order(BaseModel):
    class Status(models.TextChoices):
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        FULFILLED = 'FULFILLED', 'Fulfilled'

    class PaymentMode(models.TextChoices):
        PREPAID = 'PREPAID', 'Prepaid'
        COD = 'COD', 'Cash on delivery'

    order_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.CONFIRMED)
    payment_mode = models.CharField(max_length=32, choices=PaymentMode.choices, default=PaymentMode.PREPAID)
    cod_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    billing_address = models.ForeignKey(
        'logistics.Address',
        on_delete=models.PROTECT,
        related_name='billing_orders',
        null=True,
        blank=True,
    )
    shipping_address = models.ForeignKey(
        'logistics.Address',
        on_delete=models.PROTECT,
        related_name='shipping_orders',
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    warehouse = models.ForeignKey(
        'logistics.Warehouse',
        on_delete=models.PROTECT,
        related_name='orders',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number
