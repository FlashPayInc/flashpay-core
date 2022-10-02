from logging import getLogger
from typing import Any, Dict

from rest_framework_simplejwt.exceptions import InvalidToken

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = getLogger(__name__)


def custom_exception_handler(exception: APIException, context: Dict[str, Any]) -> Response:
    logger.exception("An exception occurred while handling request with context: %s", str(context))
    exception_response = exception_handler(exception, context)

    # exceptions not handled by DRF.
    if exception_response is None:
        return Response(
            data={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "data": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # check if exception is ValidationError
    if isinstance(exception, ValidationError):
        return Response(
            data={
                "status_code": exception_response.status_code,
                "message": "Validation Error",
                "data": exception.detail,
            },
            status=exception_response.status_code,
        )

    # token errors
    if isinstance(exception, InvalidToken):
        return Response(
            data={
                "status_code": exception_response.status_code,
                "message": exception.detail["detail"],
                "data": None,
            },
            status=exception_response.status_code,
        )

    exception_message = exception.detail if getattr(exception, "detail", None) else str(exception)
    return Response(
        data={
            "status_code": exception_response.status_code,
            "message": exception_message,
            "data": None,
        },
        status=exception_response.status_code,
    )
