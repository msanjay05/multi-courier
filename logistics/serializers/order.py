from rest_framework import serializers

from logistics.models import Order, OrderItem, Warehouse
from logistics.serializers.shipment import AddressSerializer


class OrderItemCreateSerializer(serializers.Serializer):
    sku = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    quantity = serializers.IntegerField(min_value=1, default=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    hsn_code = serializers.CharField(max_length=32, required=False, allow_blank=True, default='')
    metadata = serializers.DictField(required=False, default=dict)


class OrderItemResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'sku',
            'name',
            'description',
            'quantity',
            'unit_price',
            'tax_amount',
            'hsn_code',
            'metadata',
            'created_at',
        ]


class OrderCreateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices, required=False, default=Order.Status.CONFIRMED)
    payment_mode = serializers.ChoiceField(
        choices=Order.PaymentMode.choices,
        required=False,
        default=Order.PaymentMode.PREPAID,
    )
    cod_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    billing_address = AddressSerializer(required=False)
    shipping_address = AddressSerializer(required=False)
    warehouse_code = serializers.CharField(max_length=64, required=False, allow_blank=True)
    metadata = serializers.DictField(required=False, default=dict)
    items = OrderItemCreateSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('At least one order item is required.')
        return value

    def validate_warehouse_code(self, value):
        if not value:
            return None
        try:
            return Warehouse.objects.get(code=value, is_active=True)
        except Warehouse.DoesNotExist as exc:
            raise serializers.ValidationError('Warehouse not found or inactive.') from exc


class OrderResponseSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(read_only=True)
    items = OrderItemResponseSerializer(many=True, read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True, allow_null=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'payment_mode',
            'cod_amount',
            'total_amount',
            'warehouse_code',
            'metadata',
            'items',
            'created_at',
            'updated_at',
        ]
