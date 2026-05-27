from rest_framework.response import Response
from rest_framework.views import APIView

from logistics.serializers.shipment import ShipmentResponseSerializer
from logistics.services.shipments import get_shipment_or_raise


class ShipmentTrackView(APIView):
    def get(self, request, order_id):
        shipment = get_shipment_or_raise(order_id)
        return Response(ShipmentResponseSerializer(shipment).data)
