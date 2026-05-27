from logistics.models import BulkBatch
from logistics.tasks.bulk import process_bulk_batch


def create_bulk_batch(user, orders):
    """
    Create a BulkBatch and enqueue background processing via Celery.

    The heavy lifting (validating/filtering orders, grouping by courier partner, and
    courier API calls) happens in the Celery task.
    """
    batch = BulkBatch.objects.create(
        created_by=user,
        updated_by=user,
        total_orders=len(orders),
        order_list=orders,
    )

    # Orders are small dicts: {'order_id': str, 'courier_partner': str}
    process_bulk_batch.delay(str(batch.batch_id), user.id, orders)
    return batch
