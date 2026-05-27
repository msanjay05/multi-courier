from django.contrib import admin

from logistics.models import (
    Address,
    BulkBatch,
    BulkOrderResult,
    CourierPartner,
    Order,
    OrderItem,
    Shipment,
    ShippingItem,
    TrackingEvent,
    Warehouse,
)


admin.site.register(CourierPartner)
admin.site.register(Address)
admin.site.register(Warehouse)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Shipment)
admin.site.register(ShippingItem)
admin.site.register(TrackingEvent)
admin.site.register(BulkBatch)
admin.site.register(BulkOrderResult)

# Register your models here.
