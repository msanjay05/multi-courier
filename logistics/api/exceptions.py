from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from logistics.couriers.exceptions import CourierError
from logistics.services.exceptions import LogisticsError


def normalized_exception_handler(exc, context):
    if isinstance(exc, LogisticsError):
        return Response(
            {
                'error': {
                    'code': exc.code,
                    'message': exc.message,
                    'details': exc.details,
                }
            },
            status=exc.status_code,
        )

    if isinstance(exc, CourierError):
        return Response(
            {
                'error': {
                    'code': exc.code,
                    'message': 'Courier request could not be completed.',
                    'details': {},
                }
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    response = exception_handler(exc, context)
    if response is None:
        return None

    code = 'VALIDATION_ERROR' if response.status_code == 400 else 'API_ERROR'
    response.data = {
        'error': {
            'code': code,
            'message': 'Request validation failed.' if response.status_code == 400 else 'Request failed.',
            'details': response.data,
        }
    }
    return response
