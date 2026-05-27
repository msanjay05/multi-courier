from rest_framework.response import Response
from rest_framework.views import APIView

from logistics.serializers.shipment import ShipmentResponseSerializer
from logistics.services.shipments import cancel_shipment


class ShipmentCancelView(APIView):
    def post(self, request, order_id):
        shipment = cancel_shipment(request.user, order_id)
        return Response(ShipmentResponseSerializer(shipment).data)
