# Generated manually for Shipment -> Order one-to-one

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def link_shipments_to_orders(apps, schema_editor):
    Order = apps.get_model('logistics', 'Order')
    Shipment = apps.get_model('logistics', 'Shipment')

    for shipment in Shipment.objects.all():
        order, _ = Order.objects.get_or_create(
            order_number=shipment.internal_order_id,
            defaults={
                'payment_mode': 'PREPAID',
                'cod_amount': 0,
                'metadata': {},
            },
        )
        shipment.order_id = order.id
        shipment.save() #type: ignore


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('logistics', '0006_courier_partner_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='shipment',
            name='order',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='shipment',
                to='logistics.order',
            ),
        ),
        migrations.RunPython(link_shipments_to_orders, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='shipment',
            name='internal_order_id',
        ),
        migrations.AlterField(
            model_name='shipment',
            name='order',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='shipment',
                to='logistics.order',
            ),
        ),
    ]
