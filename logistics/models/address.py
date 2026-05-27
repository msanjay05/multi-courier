from django.db import models

from logistics.models.base import BaseModel


class Address(BaseModel):
    class AddressType(models.TextChoices):
        HOME = 'HOME', 'Home'
        OFFICE = 'OFFICE', 'Office'
        WAREHOUSE = 'WAREHOUSE', 'Warehouse'
        SELLER = 'SELLER', 'Seller'
        OTHER = 'OTHER', 'Other'

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, default='IN')
    address_type = models.CharField(max_length=32, choices=AddressType.choices, default=AddressType.OTHER)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.city} - {self.postal_code}'

    def as_dict(self):
        return {
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'line1': self.line1,
            'line2': self.line2,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
        }
