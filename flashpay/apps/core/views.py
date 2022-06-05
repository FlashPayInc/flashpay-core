from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from django.http import HttpRequest, JsonResponse


class PingView(GenericAPIView):
    def get(self, request: Request) -> Response:
        return Response(status=status.HTTP_200_OK)


def handler_404(request: HttpRequest, exception: Exception) -> JsonResponse:
    return JsonResponse(
        data={
            "status_code": status.HTTP_404_NOT_FOUND,
            "message": f"Not Found: {request.path}",
            "data": None,
        },
        status=status.HTTP_404_NOT_FOUND,
    )


def handler_500(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        data={
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal Server Error",
            "data": None,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
