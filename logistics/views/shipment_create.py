from logistics.models import ShipmentStatus
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from logistics.serializers.shipment import ShipmentCreateSerializer
from logistics.services.shipments import create_shipment


class ShipmentCreateView(APIView):
    def post(self, request):
        serializer = ShipmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order, courier_partner = serializer.validated_data['order_id'], serializer.validated_data['courier_partner']
        shipment, message = create_shipment(request.user, order, courier_partner)
        return Response({"awb":shipment.awb_number,"shipment_status":shipment.status,"message":message}, status=status.HTTP_400_BAD_REQUEST if shipment.status == ShipmentStatus.FAILED else status.HTTP_201_CREATED)
