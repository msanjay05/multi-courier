import uuid

from django.db import models

from logistics.models.base import BaseModel


class BulkBatch(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    batch_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    total_orders = models.PositiveIntegerField(default=0)
    succeeded = models.PositiveIntegerField(default=0)
    failed = models.PositiveIntegerField(default=0)
    order_list = models.JSONField(default=list)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return str(self.batch_id)


class BulkOrderResult(BaseModel):
    batch = models.ForeignKey(BulkBatch, on_delete=models.CASCADE, related_name='results')
    internal_order_id = models.CharField(max_length=100, null=True, blank=True)
    courier = models.ForeignKey(
        'logistics.CourierPartner',
        on_delete=models.PROTECT,
        related_name='bulk_order_results',
        null=True,
        blank=True,
    )
    success = models.BooleanField(default=False)
    error_code = models.CharField(max_length=64, blank=True)
    error_message = models.CharField(max_length=255, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    request_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.batch.batch_id}: {self.internal_order_id}'
