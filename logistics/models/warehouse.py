from django.db import models

from logistics.models.base import BaseModel


class Warehouse(BaseModel):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    contact_name = models.CharField(max_length=120, blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    address = models.ForeignKey('logistics.Address', on_delete=models.PROTECT, related_name='warehouses')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'
