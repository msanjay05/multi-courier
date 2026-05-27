import uuid

from django.db import IntegrityError, transaction

from logistics.models import Address, Order, OrderItem, Warehouse
from logistics.services.exceptions import LogisticsError


def _generate_order_number():
    for _ in range(10):
        candidate = f'ORD-{uuid.uuid4().hex[:12].upper()}'
        if not Order.objects.filter(order_number=candidate).exists():
            return candidate
    raise LogisticsError('Could not generate a unique order number.')


def _create_address(user, address_data):
    if not address_data:
        return None
    return Address.objects.create(
        created_by=user,
        updated_by=user,
        name=address_data['name'],
        phone=address_data['phone'],
        email=address_data.get('email', ''),
        line1=address_data['line1'],
        line2=address_data.get('line2', ''),
        city=address_data['city'],
        state=address_data['state'],
        postal_code=address_data['postal_code'],
        country=address_data.get('country', 'IN'),
    )


def create_order(user, validated_data):
    items_data = validated_data['items']
    total_amount = validated_data.get('total_amount')
    if not total_amount:
        total_amount = sum(
            (item['unit_price'] * item['quantity']) + item.get('tax_amount', 0)
            for item in items_data
        )

    order_number = _generate_order_number()
    warehouse= Warehouse.objects.get(code="DEFAULT");
    try:
        with transaction.atomic():
            billing_address = _create_address(user, validated_data.get('billing_address'))
            shipping_address = _create_address(user, validated_data.get('shipping_address'))

            order = Order.objects.create(
                created_by=user,
                updated_by=user,
                order_number=order_number,
                status=validated_data.get('status', Order.Status.CONFIRMED),
                payment_mode=validated_data.get('payment_mode', Order.PaymentMode.PREPAID),
                cod_amount=validated_data.get('cod_amount', 0),
                total_amount=total_amount,
                billing_address=billing_address,
                shipping_address=shipping_address,
                warehouse=validated_data.get('warehouse_code'),
                metadata=validated_data.get('metadata') or {},
                warehouse_id = warehouse.id
            )

            for item in items_data:
                OrderItem.objects.create(
                    created_by=user,
                    updated_by=user,
                    order=order,
                    sku=item['sku'],
                    name=item['name'],
                    description=item.get('description', ''),
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    tax_amount=item.get('tax_amount', 0),
                    hsn_code=item.get('hsn_code', ''),
                    metadata=item.get('metadata') or {},
                )
    except IntegrityError:
        order = None


    return order_number
