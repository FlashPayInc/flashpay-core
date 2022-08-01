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


class TransactionView(ListCreateAPIView):
    serializer_class = TransactionSerializer
    pagination_class = TimeStampOrderedCustomCursorPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        payment_link_uid = self.request.GET.get("payment_link", None)
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
        transactions = Transaction.objects.filter(
            txn_ref=txn_ref, status=TransactionStatus.PENDING
        )

        if not transactions.exists():
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Transaction does not exist",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transaction = transactions.first()

        # check if transaction type of 'axfer' i.e transferring algo assets
        # or 'pay' i.e transferring algo
        if (api_response["transaction"]["tx-type"] != "axfer") and (
            api_response["transaction"]["tx-type"] != "pay"
        ):
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "An error occured while setting up your account due to bad transaction provided.",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if api_response["transaction"]["tx-type"] == "axfer":
            recipient = api_response["transaction"]["asset-transfer-transaction"]["receiver"]
            amount = api_response["transaction"]["asset-transfer-transaction"]["amount"]
            asset_id = api_response["transaction"]["asset-transfer-transaction"]["asset-id"]
        else:
            recipient = api_response["transaction"]["payment-transaction"]["receiver"]
            amount = api_response["transaction"]["payment-transaction"]["amount"]
            asset_id = 0

        # check if the sender of the txn is the same as the one provided.
        if api_response["transaction"]["sender"] != transaction.sender:  # type: ignore
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "An error occured while setting up your account due to bad transaction provided.",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check if the receiver of the txn is same as the one provided.
        if recipient != transaction.recipient:  # type: ignore
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "An error occured while setting up your account due to bad transaction provided.",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check if the txn asset and amount is same as the one provided.
        if (
            amount != (transaction.amount * (10**transaction.asset.decimal))  # type: ignore
        ) or (
            asset_id != (transaction.asset.asa_id)  # type: ignore
        ):
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "An error occured while setting up your account due to bad transaction provided.",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # update transaction status and transaction hash.
        transaction.status = TransactionStatus.SUCCESS  # type: ignore
        transaction.txn_hash = txid  # type: ignore
        transaction.save(update_fields=["status", "txn_hash"])  # type: ignore
        return Response(
            data={
                "status_code": status.HTTP_200_OK,
                "message": "Transaction verified successfully",
                "data": None,
            },
            status=status.HTTP_200_OK,
        )
