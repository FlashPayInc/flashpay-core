from django.urls import path
from django.views.decorators.http import require_GET, require_POST

from flashpay.apps.payments.views import (
    PaymentLinkDetailView,
    PaymentLinkView,
    TransactionView,
    VerifyTransactionView,
)

urlpatterns = [
    path("", PaymentLinkView.as_view()),
    path("transactions", require_GET(TransactionView.as_view())),
    path("transactions/init", require_POST(TransactionView.as_view())),
    path("transactions/verify", VerifyTransactionView.as_view()),
    path("<str:uid>", PaymentLinkDetailView.as_view()),
]
