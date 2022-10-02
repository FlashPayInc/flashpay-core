from django.urls import path

from flashpay.apps.account.views import (
    AccountNetworkView,
    AccountSetUpView,
    AccountTokenRefreshView,
    AccountWalletAuthenticationView,
    APIKeyView,
    WebhookView,
)

urlpatterns = [
    path("/connect", AccountWalletAuthenticationView.as_view()),
    path("/token/refresh", AccountTokenRefreshView.as_view()),
    path("/init", AccountSetUpView.as_view()),
    path("/api-keys", APIKeyView.as_view()),
    path("/webhook", WebhookView.as_view()),
    path("/network", AccountNetworkView.as_view()),
]
