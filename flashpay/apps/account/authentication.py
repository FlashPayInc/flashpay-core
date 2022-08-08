from typing import Any, Dict, Optional, Tuple

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.settings import api_settings

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from flashpay.apps.account.models import Account, APIKey
from flashpay.apps.core.models import Network


class PublicKeyAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> Optional[Tuple[Account, Optional[str]]]:
        public_key = request.META.get("HTTP-X-PUBLIC-KEY")
        if not public_key:
            return None
        try:
            api_key = APIKey.objects.select_related("account").get(public_key=public_key)
            account = api_key.account
            request.network = Network(api_key.network)  # type: ignore
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid public key provided")
        return (account, None)


class SecretKeyAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> Optional[Tuple[Account, Optional[str]]]:
        secret_key = request.META.get("HTTP_X_SECRET_KEY")
        if not secret_key:
            return None
        try:
            api_key = APIKey.objects.select_related("account").get(secret_key=secret_key)
            request.network = Network(api_key.network)  # type: ignore
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid secret key provided")
        return (api_key.account, None)


class CustomJWTAuthentication(JWTAuthentication):  # type: ignore
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
        request.network = Network(user.network)  # type: ignore
        return user, validated_token
