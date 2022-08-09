from django.urls import path

from flashpay.apps.payments.views import (
    PaymentLinkDetailView,
    PaymentLinkView,
    TransactionsView,
    VerifyTransactionView,
)

urlpatterns = [
    path("", PaymentLinkView.as_view()),
    path("transactions", TransactionsView.as_view()),
    path("transactions/verify", VerifyTransactionView.as_view()),
    path("<str:uid>", PaymentLinkDetailView.as_view()),
]
