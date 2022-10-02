import logging
from typing import TYPE_CHECKING, Any, Dict, List, Type

from algosdk.error import IndexerHTTPError

from django.conf import settings
from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.parsers import BaseParser, FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from flashpay.apps.account.authentication import (
    AnonymousUser,
    CustomJWTAuthentication,
    PublicKeyAuthentication,
    SecretKeyAuthentication,
)
from flashpay.apps.account.models import APIKey
from flashpay.apps.core.models import Network
from flashpay.apps.core.utils import encrypt_fernet_message
from flashpay.apps.payments.models import DailyRevenue, PaymentLink, Transaction, TransactionStatus
from flashpay.apps.payments.serializers import (
    CreatePaymentLinkSerializer,
    DailyRevenueSerializer,
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
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [CustomJWTAuthentication, SecretKeyAuthentication]
    serializer_class = PaymentLinkSerializer

    def get_object(self) -> Any:
        queryset = self.filter_queryset(self.get_queryset())
        if isinstance(self.request.user, AnonymousUser):
            filter_kwargs = {"slug": self.kwargs["slug"]}
        else:
            filter_kwargs = {
                "slug": self.kwargs["slug"],
                "account": self.request.user,
                "network": self.request.network,
            }
        return get_object_or_404(queryset, **filter_kwargs)

    def retrieve(self, request: Request, *args: Dict, **kwargs: Dict) -> Response:
        payment_link = self.get_object()
        updated_data = self.get_serializer(payment_link).data
        updated_data["public_key"] = self.get_public_api_key(payment_link)

        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "Payment Link returned successfully",
                "data": updated_data,
            }
        )

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        raise MethodNotAllowed("PUT")

    def get_public_api_key(self, payment_link: PaymentLink) -> str:
        if isinstance(self.request.user, AnonymousUser):
            # there's always an api key for every account as it's auto generated on wallet setup
            pub_key = (
                APIKey.objects.filter(account=payment_link.account, network=payment_link.network)
                .first()
                .public_key  # type: ignore[union-attr]
            )
        else:
            # the conditional above already makes sure it's not `AnonymousUser`
            pub_key = (
                self.request.user.api_keys.filter(network=self.request.network).first().public_key  # type: ignore[union-attr] # noqa: E501
            )
        return encrypt_fernet_message(str(pub_key)).decode()

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        payment_link = self.get_object()
        if payment_link.is_one_time:
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

        updated_data = self.get_serializer(payment_link).data
        updated_data["public_key"] = self.get_public_api_key(payment_link)
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "Payment Link Updated",
                "data": updated_data,
            },
            status.HTTP_200_OK,
        )


class TransactionsView(ListCreateAPIView):
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
        slug = self.request.query_params.get("slug", None)
        qs = Transaction.objects.filter(
            Q(recipient=self.request.user.address) | Q(sender=self.request.user.address),  # type: ignore[union-attr]  # noqa: E501
            network=self.request.network,
        )
        if slug:
            payment_link = get_object_or_404(PaymentLink, slug=slug)
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "status_code": status.HTTP_201_CREATED,
                "message": "Transaction created successfully",
                "data": TransactionDetailSerializer(transaction).data,
            },
            status.HTTP_201_CREATED,
            headers=headers,
        )


class VerifyTransactionView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyTransactionSerializer
    transaction_serializer = TransactionDetailSerializer
    authentication_classes = [PublicKeyAuthentication, SecretKeyAuthentication]

    @property
    def indexer_client(self):  # type: ignore
        return (
            settings.TESTNET_INDEXER_CLIENT
            if self.request.network == Network.TESTNET
            else settings.MAINNET_INDEXER_CLIENT
        )

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

        # verify tx & update status and tx_hash accordingly
        try:
            if verify_transaction(db_txn=transaction, onchain_txn=api_response["transactions"][0]):
                transaction.status = TransactionStatus.SUCCESS
                transaction.txn_hash = api_response["transactions"][0]["id"]
                transaction.save(update_fields=["status", "txn_hash"])

                # check if the txn is related to a one-time payment link and disable it.
                try:
                    # at this point, a valid txn reference is expected.
                    supposed_payment_link_uid = txn_reference.split("_")[1]
                    payment_link = PaymentLink.objects.get(uid=supposed_payment_link_uid)
                    if payment_link.is_one_time and transaction.amount > 0:
                        payment_link.is_active = False
                        payment_link.save()
                except PaymentLink.DoesNotExist:
                    pass

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
                transaction.save(update_fields=["status"])
                return Response(
                    data={
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": "Transaction verification failed",
                        "data": self.transaction_serializer(transaction).data,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except IndexError:
            transaction.status = TransactionStatus.FAILED
            transaction.save(update_fields=["status"])
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Transaction verification failed",
                    "data": self.transaction_serializer(transaction).data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class DailyRevenueView(ListAPIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DailyRevenueSerializer

    def get_queryset(self) -> QuerySet:
        asa_id = self.request.query_params.get("asa_id", None)
        date_range = self.request.query_params.get("date_range")
        qs = DailyRevenue.objects.filter(
            account=self.request.user,
            asset__asa_id=asa_id,
            network=self.request.network,
        )  # type: ignore
        if date_range == "30d":
            end = timezone.now()
            start = timezone.now() - timezone.timedelta(days=30)
            qs = qs.filter(created_at__date__lte=end.date(), created_at__date_gte=start.date())
        elif date_range == "year":
            qs = qs.filter(created_at__year=timezone.now().year)
        elif date_range == "6m":
            end = timezone.now()
            start = timezone.now() - timezone.timedelta(days=30 * 6)
            qs = qs.filter(created_at__date__lte=end.date(), created_at__date_gte=start.date())
        return qs

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().list(request, *args, **kwargs)
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "Revenue returned successfully",
                "data": response.data,
            },
            status.HTTP_200_OK,
        )
