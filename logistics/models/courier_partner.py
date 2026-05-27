from django.db import models

from logistics.models.base import BaseModel


class CourierPartner(BaseModel):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.name
