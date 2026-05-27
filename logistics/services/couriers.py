from logistics.couriers import registry
from logistics.models import CourierPartner
from logistics.services.exceptions import UnknownCourierError


def get_supported_couriers():
    return registry.supported()


def resolve_courier_partner(code):
    if not code:
        raise UnknownCourierError(
            'Courier partner is required.',
            details={'supported_couriers': get_supported_couriers()},
        )

    try:
        courier = CourierPartner.objects.get(code=code, is_active=True)
    except CourierPartner.DoesNotExist as exc:
        raise UnknownCourierError(
            'Unsupported courier partner.',
            details={'supported_couriers': get_supported_couriers()},
        ) from exc

    if registry.get(code) is None:
        raise UnknownCourierError(
            'Unsupported courier partner.',
            details={'supported_couriers': get_supported_couriers()},
        )

    return courier


def get_adapter_or_raise(courier):
    adapter = registry.get(courier.code)
    if adapter is None:
        raise UnknownCourierError(
            'Unsupported courier partner.',
            details={'supported_couriers': get_supported_couriers()},
        )
    return adapter
