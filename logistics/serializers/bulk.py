from rest_framework import serializers

from logistics.models import BulkBatch, BulkOrderResult


class BulkOrderInputSerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=100)
    courier_partner = serializers.CharField(max_length=64)


class BulkCreateSerializer(serializers.Serializer):
    orders = BulkOrderInputSerializer(many=True)

    def validate_orders(self, value):
        if not value:
            raise serializers.ValidationError('At least one order is required.')
        if len(value) > 100:
            raise serializers.ValidationError('A bulk request can contain at most 100 orders.')
        seen = set()
        duplicates = []
        for order in value:
            order_id = order['order_id']
            if order_id in seen:
                duplicates.append(order_id)
            seen.add(order_id)
        if duplicates:
            raise serializers.ValidationError(f'Duplicate order_id values in request: {", ".join(duplicates)}')
        return value


class BulkOrderResultSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source='internal_order_id')
    courier_partner = serializers.CharField(source='courier.code', read_only=True, allow_null=True)

    class Meta:
        model = BulkOrderResult
        fields = [
            'order_id',
            'courier_partner',
            'success',
            'error_code',
            'error_message',
            'response_payload',
            'request_payload',
            'created_at',
        ]


class BulkBatchSerializer(serializers.ModelSerializer):
    results = BulkOrderResultSerializer(many=True, read_only=True)

    class Meta:
        model = BulkBatch
        fields = [
            'batch_id',
            'status',
            'total_orders',
            'succeeded',
            'failed',
            'results',
            'created_at',
            'updated_at',
        ]
