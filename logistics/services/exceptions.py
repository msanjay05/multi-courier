class LogisticsError(Exception):
    code = 'LOGISTICS_ERROR'
    status_code = 400

    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UnknownCourierError(LogisticsError):
    code = 'UNKNOWN_COURIER'


class ShipmentAccessError(LogisticsError):
    code = 'SHIPMENT_NOT_FOUND'
    status_code = 404


class ShipmentAlreadyCancelledError(LogisticsError):
    code = 'SHIPMENT_ALREADY_CANCELLED'
    status_code = 400


class ShipmentFailedError(LogisticsError):
    code = 'SHIPMENT_FAILED'
    status_code = 400
