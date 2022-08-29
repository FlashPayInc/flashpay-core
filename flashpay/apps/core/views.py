import logging
from typing import Any, List

from algosdk.error import AlgodHTTPError, AlgodResponseError, IndexerHTTPError

from django.conf import settings
from django.db import DatabaseError, OperationalError, connection
from django.http import HttpRequest, JsonResponse

from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from flashpay.apps.account.authentication import AssetsUploadAuthentication
from flashpay.apps.core.models import Asset
from flashpay.apps.core.serializers import AssetSerializer

logger = logging.getLogger(__name__)


class PingView(GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response(status=status.HTTP_200_OK)


class HealthCheckView(GenericAPIView):
    def get(self, request: Request) -> Response:
        try:
            connection.ensure_connection()
        except (OperationalError, DatabaseError) as e:
            logger.critical(f"Database connection down due to: {str(e)}", exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_200_OK)


class HealthCheckThirdPartyView(GenericAPIView):
    def get(self, request: Request) -> Response:
        algod_client = settings.ALGOD_CLIENT
        indexer_client = settings.INDEXER_CLIENT
        try:
            algod_client.health()
        except (AlgodHTTPError, AlgodResponseError):
            logger.critical(
                "Unable to reach Algoexplorer Node Server due to:",
                exc_info=True,
            )
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            indexer_client.health()
        except IndexerHTTPError:
            logger.critical(
                "Unable to reach Algoexplorer Indexer Server due to:",
                exc_info=True,
            )
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_200_OK)


class AssetView(ListCreateAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    pagination_class = None

    def get_authenticators(self) -> List[BaseAuthentication]:
        if self.request.method == "POST":
            return [AssetsUploadAuthentication()]
        return []

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AssetSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "status_code": status.HTTP_201_CREATED,
                "message": "Assets updated successfully",
                "data": self.get_serializer(self.get_queryset(), many=True).data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super(AssetView, self).list(request, *args, **kwargs)
        return Response(
            {
                "status_code": response.status_code,
                "message": "Assets retrieved successfully",
                "data": response.data,
            },
            status=response.status_code,
            headers=response.headers,
        )


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
