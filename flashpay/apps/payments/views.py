import logging
from typing import TYPE_CHECKING, Any, Dict, List, Type

from algosdk.error import IndexerHTTPError

from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import GenericAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import BaseParser, FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from flashpay.apps.account.authentication import (
    CustomJWTAuthentication,
    PublicKeyAuthentication,
    SecretKeyAuthentication,
)
from flashpay.apps.core.paginators import TimeStampOrderedCustomCursorPagination
from flashpay.apps.payments.models import PaymentLink, Transaction, TransactionStatus
from flashpay.apps.payments.serializers import (
    CreatePaymentLinkSerializer,
    PaymentLinkSerializer,
    TransactionDetailSerializer,
    TransactionSerializer,
    VerifyTransactionSerializer,
)
from flashpay.apps.payments.utils import verify_transaction

if TYPE_CHECKING:
    from rest_framework.authentication import BaseAuthentication
    from rest_framework.serializers import BaseSerializer

logger = logging.getLogger(__name__)


class PaymentLinkView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication, SecretKeyAuthentication]

    def get_queryset(self) -> QuerySet:
        return PaymentLink.objects.filter(account=self.request.user, network=self.request.network)  # type: ignore[misc]  # noqa: E501

    def get_serializer_class(self) -> Type["BaseSerializer"]:
        if self.request.method == "POST":
            return CreatePaymentLinkSerializer
        return PaymentLinkSerializer

    def get_parsers(self) -> List[BaseParser]:
        if self.request.method == "POST":
            return [FormParser(), MultiPartParser()]
        return super().get_parsers()

    def create(self, request: Request, *args: Dict, **kwargs: Dict) -> Response:
        serializer = self.get_serializer(data=request.data)
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
    authentication_classes = [CustomJWTAuthentication, SecretKeyAuthentication]
    serializer_class = PaymentLinkSerializer

    def get_object(self) -> Any:
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {
            "slug": self.kwargs["slug"],
            "account": self.request.user,
            "network": self.request.network,
        }
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
    pagination_class = TimeStampOrderedCustomCursorPagination
    authentication_classes = [
        PublicKeyAuthentication,
        SecretKeyAuthentication,
        CustomJWTAuthentication,
    ]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> Type["BaseSerializer"]:
        if self.request.method == "POST":
            return TransactionSerializer
        return TransactionDetailSerializer

    def get_authenticators(self) -> List["BaseAuthentication"]:
        if self.request.method == "GET":
            return super(TransactionsView, self).get_authenticators()

        return [PublicKeyAuthentication(), SecretKeyAuthentication()]

    def get_queryset(self) -> QuerySet:
        payment_link_slug = self.request.query_params.get("payment_link", None)
        qs = Transaction.objects.filter(
            recipient=self.request.user.address,  # type: ignore[union-attr]
            network=self.request.network,
        )
        if payment_link_slug:
            payment_link = get_object_or_404(PaymentLink, slug=payment_link_slug)
            qs = qs.filter(txn_reference__icontains=payment_link.uid.hex)
        return qs

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().list(request, *args, **kwargs)
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "Transactions returned successfully",
                "data": response.data,
            },
            status.HTTP_200_OK,
        )

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().create(request, *args, **kwargs)
        return Response(
            {
                "status_code": status.HTTP_201_CREATED,
                "message": "Transaction created successfully",
                "data": response.data,
            },
            status.HTTP_201_CREATED,
        )


class VerifyTransactionView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyTransactionSerializer
    indexer_client = settings.INDEXER_CLIENT
    transaction_serializer = TransactionDetailSerializer
    authentication_classes = [PublicKeyAuthentication, SecretKeyAuthentication]

    def post(self, request: Request, **kwargs: Dict[str, Any]) -> Response:
        serializer = self.get_serializer(data={"txn_reference": kwargs["txn_reference"]})
        serializer.is_valid(raise_exception=True)
        txn_reference = serializer.validated_data["txn_reference"]

        try:
            transaction = Transaction.objects.get(txn_reference=txn_reference)
        except Transaction.DoesNotExist:
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Transaction reference is invalid",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            api_response = self.indexer_client.search_transactions(
                note_prefix=txn_reference.encode(),
                address=transaction.sender,
                address_role="sender",
            )
        except IndexerHTTPError as e:
            logger.error(
                f"Error finding transaction with "
                f'transaction id: {serializer.validated_data["txn_reference"]} '
                f"due to: {str(e)}"
            )
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Transaction reference is invalid",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if transaction has already been verified
        if transaction.status != TransactionStatus.PENDING:
            return Response(
                data={
                    "status_code": status.HTTP_409_CONFLICT,
                    "message": "Transaction has already been verified",
                    "data": self.transaction_serializer(transaction).data,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # verify tx & update status and tx_hash accordingly
        if verify_transaction(db_txn=transaction, onchain_txn=api_response["transactions"][0]):
            transaction.status = TransactionStatus.SUCCESS
            transaction.txn_hash = txn_reference
            transaction.save(update_fields=["status", "txn_hash"])
            return Response(
                data={
                    "status_code": status.HTTP_200_OK,
                    "message": "Transaction verified successfully",
                    "data": self.transaction_serializer(transaction).data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            transaction.status = TransactionStatus.FAILED
            transaction.txn_hash = txn_reference
            transaction.save(update_fields=["status", "txn_hash"])
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Transaction verification failed",
                    "data": self.transaction_serializer(transaction).data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
