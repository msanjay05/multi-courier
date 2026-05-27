from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Order',
            new_name='Shipment',
        ),
        migrations.RenameField(
            model_name='trackingevent',
            old_name='order',
            new_name='shipment',
        ),
        migrations.RenameField(
            model_name='bulkorderresult',
            old_name='order',
            new_name='shipment',
        ),
        migrations.RemoveConstraint(
            model_name='shipment',
            name='unique_order_per_owner',
        ),
        migrations.AlterField(
            model_name='shipment',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shipments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='shipment',
            constraint=models.UniqueConstraint(fields=('owner', 'internal_order_id'), name='unique_shipment_per_owner'),
        ),
    ]
