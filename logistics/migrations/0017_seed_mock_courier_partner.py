from django.db import migrations


def seed_mock_courier_partner(apps, schema_editor):
    CourierPartner = apps.get_model('logistics', 'CourierPartner')
    CourierPartner.objects.get_or_create(
        code='mock',
        defaults={'name': 'MockCourier', 'is_active': True},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0016_alter_bulkorderresult_internal_order_id'),
    ]

    operations = [
        migrations.RunPython(seed_mock_courier_partner, migrations.RunPython.noop),
    ]

