import logging
from typing import TYPE_CHECKING, Any, Dict, Type

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from flashpay.apps.core.paginators import TimeStampOrderedCustomCursorPagination
from flashpay.apps.payments.models import PaymentLink, PaymentLinkTransaction
from flashpay.apps.payments.serializers import (
    CreatePaymentLinkSerializer,
    PaymentLinkSerializer,
    PaymentLinkTransactionSerializer,
)

if TYPE_CHECKING:
    from rest_framework.serializers import BaseSerializer

logger = logging.getLogger(__name__)


class PaymentLinkView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return PaymentLink.objects.filter(account__address=self.request.user.id)

    def get_serializer_class(self) -> Type["BaseSerializer"]:
        if self.request.method == "POST":
            return CreatePaymentLinkSerializer
        return PaymentLinkSerializer

    def create(self, request: Request, *args: Dict, **kwargs: Dict) -> Response:
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "status_code": status.HTTP_201_CREATED,
                "message": "Payment Link Created Successfully",
                "data": None,
            },
            status.HTTP_201_CREATED,
        )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().list(request, *args, **kwargs)
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "Payment links returned successfully",
                "data": response.data,
            },
            status.HTTP_200_OK,
        )


class PaymentLinkDetailView(RetrieveUpdateAPIView):
    queryset = PaymentLink.objects.get_queryset()
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentLinkSerializer

    def get_object(self) -> Any:
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {"uid": self.kwargs["uid"], "account__address": self.request.user.id}
        return get_object_or_404(queryset, **filter_kwargs)

    def retrieve(self, request: Request, *args: Dict, **kwargs: Dict) -> Response:
        payment_link = self.get_object()
        serializer = self.get_serializer(payment_link)
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": None,
                "data": serializer.data,
            }
        )

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        raise MethodNotAllowed("PUT")

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        payment_link = self.get_object()
        if payment_link.is_one_time and payment_link.total_revenue == payment_link.amount:
            return Response(
                {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "You cannot modify a one-time payment link's status.",
                    "data": None,
                },
                status.HTTP_400_BAD_REQUEST,
            )
        payment_link.is_active = not payment_link.is_active
        payment_link.save()
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "Payment Link Updated",
                "data": self.get_serializer(payment_link).data,
            },
            status.HTTP_200_OK,
        )


class PaymentLinkTransactionView(ListAPIView):
    serializer_class = PaymentLinkTransactionSerializer
    pagination_class = TimeStampOrderedCustomCursorPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        uid = self.kwargs.get("uid")
        return PaymentLinkTransaction.objects.filter(
            payment_link__uid=uid,
            payment_link__account__address=self.request.user.id,
        )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().list(request, *args, **kwargs)
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "Transactions for payment link returned successfully",
                "data": response.data,
            },
            status.HTTP_200_OK,
        )
