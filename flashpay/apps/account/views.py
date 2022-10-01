import logging
from base64 import b64encode
from typing import TYPE_CHECKING, Any, Optional, Sequence, Type

from algosdk.error import IndexerHTTPError
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings
from django.db.models import QuerySet

from rest_framework import status
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from flashpay.apps.account.authentication import CustomJWTAuthentication
from flashpay.apps.account.models import Account, APIKey
from flashpay.apps.account.serializers import (
    AccountNetworkUpdateSerializer,
    AccountSetUpSerializer,
    AccountWalletAuthenticationSerializer,
    APIKeySerializer,
    CreateAPIKeySerializer,
)
from flashpay.apps.account.utils import generate_api_key
from flashpay.apps.core.models import Network

if TYPE_CHECKING:
    from rest_framework.permissions import _PermissionClass
    from rest_framework.serializers import BaseSerializer

logger = logging.getLogger(__name__)


class AccountWalletAuthenticationView(GenericAPIView):
    queryset = Account.objects.get_queryset()
    serializer_class: Optional[Type["BaseSerializer"]] = AccountWalletAuthenticationSerializer
    permission_classes: Sequence["_PermissionClass"] = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account, _ = self.get_queryset().get_or_create(
            address=serializer.validated_data["address"],
        )
        if account.is_verified is False:
            return Response(
                data={
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "message": "Please set up your wallet and try again.",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # switch to jwt auth if account is verified
        refresh = RefreshToken.for_user(account)
        return Response(
            data={
                "status_code": status.HTTP_200_OK,
                "message": "",
                "data": {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                },
            },
            status=status.HTTP_200_OK,
        )


class AccountSetUpView(GenericAPIView):
    queryset = Account.objects.get_queryset()
    serializer_class: Optional[Type["BaseSerializer"]] = AccountSetUpSerializer
    permission_classes: Sequence["_PermissionClass"] = [AllowAny]

    def get_indexer_client(self, network: Network) -> Any:
        return (
            settings.TESTNET_INDEXER_CLIENT
            if network == Network.TESTNET
            else settings.MAINNET_INDEXER_CLIENT
        )

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            account = self.get_queryset().get(
                address=serializer.validated_data["address"],
            )
        except Account.DoesNotExist:
            return Response(
                data={
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "message": f"Sorry, account with address {serializer.validated_data['address']} not found!",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if account.is_verified is True:
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Your account has already been set up.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        indexer_client = self.get_indexer_client(Network.MAINNET)
        try:
            api_response = indexer_client.transaction(
                txid=serializer.validated_data["txid"],
            )
        except IndexerHTTPError as e:
            logger.error(
                f"Error setting up address: {account.address} using "
                f'transaction id: {serializer.validated_data["txid"]} with '
                f'nonce: {serializer.validated_data["nonce"]} due to: {str(e)}'
            )
            return Response(
                data={
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "An error occured while setting up your account",
                    "data": None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # check if transaction type of 'pay' i.e sending & receiving ALGO.
        if api_response["transaction"]["tx-type"] != "pay":
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "An error occured while setting up your account due to bad transaction provided.",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check if the sender of the txn is the same as the one provided in the payload.
        if api_response["transaction"]["sender"] != account.address:
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "An error occured while setting up your account due to bad transaction provided.",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check if the receiver of the txn is FLASHPAY.
        if (
            api_response["transaction"]["payment-transaction"]["receiver"]
            != settings.FLASHPAY_MASTER_WALLET
        ):
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "An error occured while setting up your account due to bad transaction provided.",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check if the transaction note matches the nonce generated.
        tx_note = api_response["transaction"].get("note")
        if (
            tx_note is None
            or tx_note != b64encode(serializer.validated_data["nonce"].encode()).decode()
        ):
            return Response(
                data={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "An error occured while setting up your account due to bad transaction provided.",  # noqa: E501
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # generate api keys
        mainnet_api_keys = generate_api_key(address=account.address, network=Network.MAINNET)
        testnet_api_keys = generate_api_key(address=account.address, network=Network.TESTNET)
        account.api_keys.create(
            secret_key=mainnet_api_keys[0],
            public_key=mainnet_api_keys[1],
            network=Network.MAINNET,
        )
        account.api_keys.create(
            secret_key=testnet_api_keys[0],
            public_key=testnet_api_keys[1],
            network=Network.TESTNET,
        )

        account.is_verified = True
        account.save()
        return Response(
            data={
                "status_code": status.HTTP_200_OK,
                "message": "Your account was set up successfully",
                "data": None,
            },
            status=status.HTTP_200_OK,
        )


class APIKeyView(ListCreateAPIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return APIKey.objects.filter(account=self.request.user, network=self.request.network)  # type: ignore[misc] # noqa: E501

    def get_serializer_class(self) -> Type["BaseSerializer"]:
        if self.request.method == "POST":
            return CreateAPIKeySerializer
        return APIKeySerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().list(request, *args, **kwargs)
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "API Keys fetched successfully.",
                "data": response.data,
            },
            status.HTTP_200_OK,
        )

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().create(request, *args, **kwargs)
        return Response(
            {
                "status_code": status.HTTP_201_CREATED,
                "message": "API Key created successfully.",
                "data": response.data,
            },
            status.HTTP_201_CREATED,
        )


class AccountNetworkView(GenericAPIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = AccountNetworkUpdateSerializer

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.network = Network(serializer.validated_data["network"])  # type: ignore[union-attr] # noqa: E501
        self.request.user.save()

        return Response(
            data={
                "status": status.HTTP_200_OK,
                "message": "Network updated successfully!",
                "data": {"network": self.request.user.network},  # type: ignore[union-attr] # noqa: E501
            },
            status=status.HTTP_200_OK,
        )

    def get(self, request: Request) -> Response:
        return Response(
            data={
                "status": status.HTTP_200_OK,
                "message": "Network status returned successfully!",
                "data": {"network": self.request.user.network},  # type: ignore[union-attr] # noqa: E501
            },
            status=status.HTTP_200_OK,
        )
