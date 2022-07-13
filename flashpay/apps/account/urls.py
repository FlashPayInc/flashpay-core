from rest_framework_simplejwt.views import TokenBlacklistView

from django.urls import path

from flashpay.apps.account.views import AccountSetUpView, AccountWalletAuthenticationView

urlpatterns = [
    path("connect", AccountWalletAuthenticationView.as_view()),
    path("disconnect", TokenBlacklistView.as_view()),
    path("init", AccountSetUpView.as_view()),
]
