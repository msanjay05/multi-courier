from rest_framework import serializers

from logistics.models import CourierPartner, Order, Shipment, ShipmentStatus, TrackingEvent


class AddressSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=30)
    email = serializers.EmailField(required=False, allow_blank=True)
    line1 = serializers.CharField(max_length=255)
    line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=2, default='IN')


class ParcelSerializer(serializers.Serializer):
    weight_kg = serializers.DecimalField(max_digits=8, decimal_places=2)
    length_cm = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    width_cm = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    height_cm = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    declared_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['__all__']

class CourierPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourierPartner
        fields = ['__all__']

class ShipmentCreateSerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=100)
    courier_partner = serializers.CharField(max_length=64)
    def validate_order_id(self, value):
        try:
            order = Order.objects.select_related(
                'shipping_address',
                'billing_address',
                'warehouse__address',
            ).get(order_number=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("This Order ID does not exist.")
        return order
    def validate_courier_partner(self, value):
        try:
            courier_partner = CourierPartner.objects.get(code=value)
        except CourierPartner.DoesNotExist:
            raise serializers.ValidationError("This Courier Partner does not exist.")
        return courier_partner


class ShipmentStatusWebhookSerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=100, required=False)
    awb_number = serializers.CharField(max_length=128, required=False)
    status = serializers.CharField(max_length=32)
    message = serializers.CharField(max_length=255, required=False, allow_blank=True)
    location = serializers.CharField(max_length=255, required=False, allow_blank=True)
    occurred_at = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        if not attrs.get('order_id') and not attrs.get('awb_number'):
            raise serializers.ValidationError('Webhook must include `order_id` or `awb_number`.')
        return attrs


class TrackingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingEvent
        fields = ['status', 'message', 'location', 'raw_payload', 'occurred_at', 'created_at']


class ShipmentResponseSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source='order.order_number')
    courier_partner = serializers.CharField(source='courier.code', read_only=True)
    tracking_history = TrackingEventSerializer(source='tracking_events', many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'order_id',
            'courier_partner',
            'courier_order_id',
            'awb_number',
            'status',
            'tracking_history'
        ]
