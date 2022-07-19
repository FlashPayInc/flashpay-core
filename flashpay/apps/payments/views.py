import logging
from typing import TYPE_CHECKING, Dict, Optional, Sequence, Type

from django.db.models import QuerySet

from rest_framework import status
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from flashpay.apps.core.paginators import TimeStampOrderedCustomCursorPagination
from flashpay.apps.payments.models import PaymentLink, PaymentLinkTransaction
from flashpay.apps.payments.serializers import (
    CreatePaymentLinkSerializer,
    PaymentLinkDetailSerializer,
    PaymentLinkSerializer,
    PaymentLinkTransactionSerializer,
)

if TYPE_CHECKING:
    from rest_framework.permissions import _PermissionClass
    from rest_framework.serializers import BaseSerializer

logger = logging.getLogger(__name__)


class PaymentLinkView(ListCreateAPIView):

    serializer_class: Optional[Type["BaseSerializer"]] = PaymentLinkSerializer
    permission_classes: Sequence["_PermissionClass"] = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return PaymentLink.objects.filter(account__address=self.request.user.id)  # type: ignore

    def create(self, request: Request, *args: Dict, **kwargs: Dict) -> Response:
        ser = CreatePaymentLinkSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        link = ser.save()
        return Response(
            {
                "status_code": status.HTTP_201_CREATED,
                "message": "Payment Link Created Successfully",
                "data": PaymentLinkSerializer(link).data,
            },
            status.HTTP_201_CREATED,
        )


class PaymentLinkDetailView(RetrieveUpdateAPIView):

    permission_classes: Sequence["_PermissionClass"] = [IsAuthenticated]

    def retrieve(self, request: Request, *args: Dict, **kwargs: Dict) -> Response:
        try:
            link = PaymentLink.objects.get(
                uid=kwargs["uid"], account__address=request.user.id  # type: ignore
            )
        except PaymentLink.DoesNotExist:
            return Response(
                {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "message": "Payment Link Not Found",
                    "data": None,
                },
                status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": None,
                "data": PaymentLinkDetailSerializer(link).data,
            }
        )

    def update(self, request: Request, *args: Dict, **kwargs: Dict) -> Response:
        try:
            link = PaymentLink.objects.get(
                uid=kwargs["uid"], account__address=request.user.id  # type: ignore
            )
        except PaymentLink.DoesNotExist:
            return Response(
                {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "message": "Payment Link Not Found",
                    "data": None,
                },
                status.HTTP_404_NOT_FOUND,
            )
        link.is_active = not link.is_active
        link.save()
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "Payment Link Updated",
                "data": PaymentLinkDetailSerializer(link).data,
            },
            status.HTTP_200_OK,
        )


class PaymentLinkTransactionView(ListAPIView):

    serializer_class: Optional[Type["BaseSerializer"]] = PaymentLinkTransactionSerializer
    pagination_class = TimeStampOrderedCustomCursorPagination
    permission_classes: Sequence["_PermissionClass"] = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        uid = self.kwargs.get("uid")
        return PaymentLinkTransaction.objects.filter(
            payment_link__uid=uid,
            payment_link__account__address=self.request.user.id,  # type: ignore
        )
