from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from logistics.serializers.bulk import BulkBatchSerializer, BulkCreateSerializer
from logistics.services.bulk import create_bulk_batch


class BulkCreateView(APIView):
    def post(self, request):
        serializer = BulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        batch = create_bulk_batch(request.user, serializer.validated_data['orders'])
        return Response(BulkBatchSerializer(batch).data, status=status.HTTP_202_ACCEPTED)
