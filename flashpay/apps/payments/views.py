import logging
from base64 import b64decode
from typing import TYPE_CHECKING, Any, Dict, Type

from algosdk.error import IndexerHTTPError
from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import GenericAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from flashpay.apps.core.paginators import TimeStampOrderedCustomCursorPagination
from flashpay.apps.payments.models import PaymentLink, Transaction, TransactionStatus
from flashpay.apps.payments.serializers import (
    CreatePaymentLinkSerializer,
    PaymentLinkSerializer,
    TransactionSerializer,
    VerifyTransactionSerializer,
)
from flashpay.apps.payments.utils import verify_txn

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


class TransactionsView(ListCreateAPIView):
    serializer_class = TransactionSerializer
    pagination_class = TimeStampOrderedCustomCursorPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        payment_link_uid = self.request.query_params.get("payment_link", None)
        qs = Transaction.objects.filter(
            recipient=self.request.user.id,
        )
        if payment_link_uid:
            payment_link = get_object_or_404(PaymentLink, uid=payment_link_uid)
            qs = qs.filter(txn_ref__icontains=payment_link.uid.hex)
        return qs

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


class VerifyTransactionView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyTransactionSerializer

    def post(self, request: Request, format: Any = None) -> Response:
        indexer_client = settings.INDEXER_CLIENT
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        txid = serializer.validated_data["txid"]

        try:
            api_response = indexer_client.transaction(
                txid=txid,
            )
        except IndexerHTTPError as e:
            logger.error(
                f"Error finding transaction with"
                f'transaction id: {serializer.validated_data["txid"]}'
                f"due to: {str(e)}"
            )
            return Response(
                data={
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "Could not find transaction",
                    "data": None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        tx_note = api_response["transaction"].get("note")
        txn_ref = b64decode(tx_note).decode()

        try:
            transaction = Transaction.objects.get(
                txn_ref=txn_ref
            )
        except Transaction.DoesNotExist:
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Transaction does not exist",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if transaction has already been verified
        if transaction.status != TransactionStatus.PENDING:
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Transaction has already been verified",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )



        txn = api_response["transaction"]

        if verify_txn(transaction=transaction, txn=txn):
            # update transaction status and transaction hash.
            transaction.status = TransactionStatus.SUCCESS
            transaction.txn_hash = txid
            transaction.save(update_fields=["status", "txn_hash"])
            return Response(
                data={
                    "status_code": status.HTTP_200_OK,
                    "message": "Transaction verified successfully",
                    "data": None,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Transaction could not be verified due to bad transaction provided.",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
