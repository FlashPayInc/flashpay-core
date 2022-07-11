from django.urls import path

from flashpay.apps.payments.views import (
    PaymentLinkDetailView,
    PaymentLinkTransactionView,
    PaymentLinkView,
)

urlpatterns = [
    path("<str:uid>/transactions", PaymentLinkTransactionView.as_view(), name="payment-link-txns"),
    path("<str:uid>", PaymentLinkDetailView.as_view(), name="retrieve-update-link"),
    path("", PaymentLinkView.as_view(), name="payment-link"),
]
