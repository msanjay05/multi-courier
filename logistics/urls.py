from django.urls import path

from logistics.views.bulk_create import BulkCreateView
from logistics.views.login import LoginView
from logistics.views.order_create import OrderCreateView
from logistics.views.shipment_cancel import ShipmentCancelView
from logistics.views.shipment_create import ShipmentCreateView
from logistics.views.shipment_webhook import ShipmentStatusWebhookView
from logistics.views.shipment_track import ShipmentTrackView
from logistics.views.signup import SignupView

urlpatterns = [
    path('auth/signup/', SignupView.as_view(), name='signup'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('order/', OrderCreateView.as_view(), name='order-create'),
    path('shipment/', ShipmentCreateView.as_view(), name='shipment-create'),
    path('shipment/webhook/', ShipmentStatusWebhookView.as_view(), name='shipment-webhook'),
    path('shipment/bulk/', BulkCreateView.as_view(), name='bulk-create'),
    path('shipment/<str:order_id>/track/', ShipmentTrackView.as_view(), name='shipment-track'),
    path('shipment/<str:order_id>/cancel/', ShipmentCancelView.as_view(), name='shipment-cancel'),
]
