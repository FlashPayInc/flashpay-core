from django.urls import path

from flashpay.apps.account.views import (
    AccountSetUpView,
    AccountWalletAuthenticationView,
    APIKeyView,
)

urlpatterns = [
    path("connect", AccountWalletAuthenticationView.as_view()),
    path("init", AccountSetUpView.as_view()),
    path("api-keys", APIKeyView.as_view()),
]
