import logging
import time

logger = logging.getLogger('logistics.request')


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()

        logger.info(
            'Request started method=%s path=%s',
            request.method,
            request.path,
        )

        try:
            response = self.get_response(request)
        except Exception:
            duration_ms = round((time.monotonic() - start) * 1000, 2)
            logger.exception(
                'Request failed method=%s path=%s duration_ms=%s',
                request.method,
                request.path,
                duration_ms,
                
            )
            raise

        duration_ms = round((time.monotonic() - start) * 1000, 2)
        message = (
            'Request completed method=%s path=%s status=%s duration_ms=%s'
        )
        log_args = (request.method, request.path, response.status_code, duration_ms)

        if response.status_code >= 400:
            logger.error(message, *log_args)
        else:
            logger.info(message, *log_args)

        return response
