# type: ignore  #mfjpm
# TODO: Figure a way to make mypy happy here.
# Perhaps generate a stub for rest_framework_simplejwt.
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, Token
from rest_framework_simplejwt.utils import datetime_from_epoch

from flashpay.apps.account.models import CustomBlacklistedToken, CustomOutstandingToken


class BlacklistMixin:
    """
    This is a port of `BlacklistMixin` from jazzband/restframework-simplejwt.
    https://github.com/jazzband/djangorestframework-simplejwt/blob/7740384168d41736044562c9bf1749b3bf8cd941/rest_framework_simplejwt/tokens.py#L207
    """

    def verify(self, *args, **kwargs):
        self.check_blacklist()

        super().verify(*args, **kwargs)

    def check_blacklist(self):
        jti = self.payload[api_settings.JTI_CLAIM]

        if CustomBlacklistedToken.objects.filter(token__jti=jti).exists():
            raise TokenError("Token is blacklisted")

    def blacklist(self):
        jti = self.payload[api_settings.JTI_CLAIM]
        exp = self.payload["exp"]

        token, _ = CustomOutstandingToken.objects.get_or_create(
            jti=jti,
            defaults={
                "token": str(self),
                "expires_at": datetime_from_epoch(exp),
            },
        )

        return CustomBlacklistedToken.objects.get_or_create(token=token)

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)

        jti = token[api_settings.JTI_CLAIM]
        exp = token["exp"]

        CustomOutstandingToken.objects.create(
            user=user,
            jti=jti,
            token=str(token),
            created_at=token.current_time,
            expires_at=datetime_from_epoch(exp),
        )

        return token


class CustomRefreshToken(BlacklistMixin, Token):
    """
    A port of
    https://github.com/jazzband/djangorestframework-simplejwt/blob/7740384168d41736044562c9bf1749b3bf8cd941/rest_framework_simplejwt/tokens.py#L293
    """

    token_type = "refresh"
    lifetime = api_settings.REFRESH_TOKEN_LIFETIME
    no_copy_claims = (
        api_settings.TOKEN_TYPE_CLAIM,
        "exp",
        api_settings.JTI_CLAIM,
        "jti",
    )
    access_token_class = AccessToken

    @property
    def access_token(self):
        access = self.access_token_class()
        access.set_exp(from_time=self.current_time)

        no_copy = self.no_copy_claims
        for claim, value in self.payload.items():
            if claim in no_copy:
                continue
            access[claim] = value

        return access
