from typing import Any, Dict

from django.http import Http404

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exception: APIException, context: Dict[str, Any]) -> Response:
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

    if isinstance(exception, Http404):
        return Response(
            data={
                "status_code": exception_response.status_code,
                "message": str(exception),
                "data": None,
            },
            status=exception_response.status_code,
        )
    return Response(
        data={
            "status_code": exception_response.status_code,
            "message": exception.detail,
            "data": None,
        },
        status=exception_response.status_code,
    )
