from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from logistics.serializers.order import OrderCreateSerializer, OrderResponseSerializer
from logistics.services.orders import create_order


class OrderCreateView(APIView):
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_number = create_order(request.user, serializer.validated_data)
        return Response(
            {"order_number": order_number},
            status=status.HTTP_201_CREATED,
        )
