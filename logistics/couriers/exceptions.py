class CourierError(Exception):
    code = 'COURIER_ERROR'

    def __init__(self, message, raw_payload=None, retryable=False):
        super().__init__(message)
        self.message = message
        self.raw_payload = raw_payload or {}
        self.retryable = retryable


class CourierValidationError(CourierError):
    code = 'COURIER_VALIDATION_ERROR'


class CourierAuthError(CourierError):
    code = 'COURIER_AUTH_ERROR'


class CourierTemporaryError(CourierError):
    code = 'COURIER_TEMPORARY_ERROR'

    def __init__(self, message, raw_payload=None):
        super().__init__(message, raw_payload=raw_payload, retryable=True)
