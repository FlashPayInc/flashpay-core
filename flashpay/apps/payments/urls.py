from django.urls import path

from flashpay.apps.payments.views import (
    PaymentLinkDetailView,
    PaymentLinkTransactionView,
    PaymentLinkView,
)

urlpatterns = [
    path("", PaymentLinkView.as_view()),
    path("<str:uid>/transactions", PaymentLinkTransactionView.as_view()),
    path("<str:uid>", PaymentLinkDetailView.as_view()),
]
