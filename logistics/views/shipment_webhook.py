from django.conf import settings
from rest_framework import status as http_status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from logistics.serializers.shipment import (
    ShipmentResponseSerializer,
    ShipmentStatusWebhookSerializer,
)
from logistics.services.shipments import apply_webhook_status_update


class ShipmentStatusWebhookView(APIView):
    """
    Webhook endpoint for courier status updates.

    - Does NOT call the courier tracking APIs.
    - Updates `Shipment.status` and appends a `TrackingEvent`.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        secret = getattr(settings, 'COURIER_WEBHOOK_SECRET', '') or ''
        if secret:
            incoming_secret = request.headers.get('X-Webhook-Secret') or request.META.get('HTTP_X_WEBHOOK_SECRET')
            if incoming_secret != secret:
                return Response(
                    {
                        'error': {
                            'code': 'INVALID_WEBHOOK_SECRET',
                            'message': 'Invalid webhook secret.',
                            'details': {},
                        }
                    },
                    status=http_status.HTTP_403_FORBIDDEN,
                )

        serializer = ShipmentStatusWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data


        shipment = apply_webhook_status_update(
            user=request.user if getattr(request.user, 'is_authenticated', False) else None,
            order_id=v.get('order_id'),
            awb_number=v.get('awb_number'),
            status=v['status'],
            message=v.get('message', '') or '',
            location=v.get('location', '') or '',
            raw_payload=request.data,
            occurred_at=v.get('occurred_at'),
        )
        return Response(ShipmentResponseSerializer(shipment).data, status=http_status.HTTP_200_OK)

