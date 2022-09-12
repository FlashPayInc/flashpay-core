import binascii
from base64 import b64decode
from typing import Any, Dict, Optional, Tuple

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.settings import api_settings

from django.conf import settings
from django.db.models import Q

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from flashpay.apps.account.models import Account, APIKey
from flashpay.apps.core.models import Network


class PublicKeyAuthentication(BaseAuthentication):
    www_authenticate_realm = "api"

    def authenticate_header(self, request: Request) -> Optional[str]:
        return f'X-PUBLIC-KEY realm="{self.www_authenticate_realm}"'

    def authenticate(self, request: Request) -> Optional[Tuple[Account, Optional[str]]]:
        public_key = request.META.get("HTTP_X_PUBLIC_KEY")
        if not public_key:
            return None
        try:
            # in some cases like `payment link detail view`, the base64 encoded format of the
            # public key can be used.
            try:
                public_key_query = Q(public_key=b64decode(public_key).decode())
            except binascii.Error:
                public_key_query = Q(public_key=public_key)
            api_key = APIKey.objects.select_related("account").get(public_key_query)
            account = api_key.account
            request.network = Network(api_key.network)  # type: ignore[attr-defined]
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid public key provided")
        return account, None


class SecretKeyAuthentication(BaseAuthentication):
    www_authenticate_realm = "api"

    def authenticate_header(self, request: Request) -> Optional[str]:
        return f'X-SECRET-KEY realm="{self.www_authenticate_realm}"'

    def authenticate(self, request: Request) -> Optional[Tuple[Account, Optional[str]]]:
        secret_key = request.META.get("HTTP_X_SECRET_KEY")
        if not secret_key:
            return None
        try:
            api_key = APIKey.objects.select_related("account").get(secret_key=secret_key)
            request.network = Network(api_key.network)  # type: ignore[attr-defined]
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid secret key provided")
        return api_key.account, None


class CustomJWTAuthentication(JWTAuthentication):  # type: ignore[no-any-unimported]
    def __init__(self, *args: Dict, **kwargs: Dict) -> None:
        super().__init__(*args, **kwargs)
        self.user_model = Account

    def get_user(self, validated_token: Any) -> Optional[Account]:
        try:
            account_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken("Token contained no recognizable user identification")

        try:
            account = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: account_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed("User not found")
        return account

    def authenticate(self, request: Request) -> Optional[Tuple[Account, str]]:
        response = super().authenticate(request)
        if response is None:
            return response
        user, validated_token = response
        request.network = Network(user.network)  # type: ignore[attr-defined]
        return user, validated_token


class AnonymousUser:
    id = None
    pk = None
    address = ""
    is_verified = False

    def __str__(self) -> str:
        return "AnonymousAccount"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__)

    def __hash__(self) -> int:
        return 1  # instances always return the same hash value

    @property
    def is_anonymous(self) -> bool:
        return True

    @property
    def is_authenticated(self) -> bool:
        return False


class AssetsUploadAPiUser(AnonymousUser):
    @property
    def is_authenticated(self) -> bool:
        return True


class AssetsUploadAuthentication(BaseAuthentication):
    www_authenticate_realm = "api"

    def authenticate_header(self, request: Request) -> Optional[str]:
        return f'Token realm="{self.www_authenticate_realm}"'

    def authenticate(self, request: Request) -> Optional[Tuple["AnonymousUser", Any]]:
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if auth_header is None:
            raise AuthenticationFailed("Missing API Key")
        api_key = auth_header.split(" ")[-1].strip()
        if api_key != settings.ASSETS_UPLOAD_API_KEY:
            raise AuthenticationFailed("Invalid API Key provided")
        return AssetsUploadAPiUser(), None
