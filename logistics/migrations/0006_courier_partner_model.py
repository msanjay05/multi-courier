# Generated manually for CourierPartner rollout

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def seed_courier_partners(apps, schema_editor):
    CourierPartner = apps.get_model('logistics', 'CourierPartner')
    CourierPartner.objects.get_or_create(
        code='urbanebolt',
        defaults={'name': 'UrbaneBolt', 'is_active': True},
    )


def dedupe_unique_fields(apps, schema_editor):
    for model_name, field_name in (
        ('Shipment', 'internal_order_id'),
        ('Order', 'order_number'),
        ('Warehouse', 'code'),
    ):
        model = apps.get_model('logistics', model_name)
        seen = set()
        for row in model.objects.order_by('id'):
            value = getattr(row, field_name)
            if value in seen:
                row.delete()
            else:
                seen.add(value)


def link_courier_foreign_keys(apps, schema_editor):
    CourierPartner = apps.get_model('logistics', 'CourierPartner')
    Shipment = apps.get_model('logistics', 'Shipment')
    BulkOrderResult = apps.get_model('logistics', 'BulkOrderResult')

    partners = {partner.code: partner for partner in CourierPartner.objects.all()}
    default_partner = partners.get('urbanebolt')

    for shipment in Shipment.objects.all():
        partner = partners.get(shipment.courier_partner) or default_partner
        if partner:
            shipment.courier_id = partner.id
            shipment.save()

    for result in BulkOrderResult.objects.all():    
        if not result.courier_partner:
            continue
        partner = partners.get(result.courier_partner)
        if partner:
            result.courier_id = partner.id
            result.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('logistics', '0005_remove_owner'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourierPartner',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.SlugField(max_length=64, unique=True)),
                ('name', models.CharField(max_length=120)),
                ('is_active', models.BooleanField(default=True)),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='%(app_label)s_%(class)s_created',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'updated_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='%(app_label)s_%(class)s_updated',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['code'],
                'abstract': False,
            },
        ),
        migrations.RunPython(seed_courier_partners, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name='order',
            name='unique_order_number_per_creator',
        ),
        migrations.RemoveConstraint(
            model_name='shipment',
            name='unique_shipment_per_creator',
        ),
        migrations.RemoveConstraint(
            model_name='warehouse',
            name='unique_warehouse_code_per_creator',
        ),
        migrations.AddField(
            model_name='shipment',
            name='courier',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='shipments',
                to='logistics.courierpartner',
            ),
        ),
        migrations.AddField(
            model_name='bulkorderresult',
            name='courier',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='bulk_order_results',
                to='logistics.courierpartner',
            ),
        ),
        migrations.RunPython(link_courier_foreign_keys, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='shipment',
            name='courier_partner',
        ),
        migrations.RemoveField(
            model_name='bulkorderresult',
            name='courier_partner',
        ),
        migrations.RunPython(dedupe_unique_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='shipment',
            name='courier',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='shipments',
                to='logistics.courierpartner',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='internal_order_id',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='code',
            field=models.CharField(max_length=64, unique=True),
        ),
    ]
