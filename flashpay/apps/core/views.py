import logging
from typing import Optional, Type

from algosdk.error import AlgodHTTPError, AlgodResponseError, IndexerHTTPError

from django.conf import settings
from django.db import DatabaseError, OperationalError, connection, models
from django.http import HttpRequest, JsonResponse

from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from flashpay.apps.core.models import Asset
from flashpay.apps.core.serializers import AssetSerializer

logger = logging.getLogger(__name__)


class PingView(GenericAPIView):
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


class AssetView(ListAPIView):

    queryset: models.QuerySet = Asset.objects.all()
    serializer_class: Optional[Type[BaseSerializer]] = AssetSerializer
    pagination_class = None


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
