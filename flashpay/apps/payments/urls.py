from django.urls import path

from flashpay.apps.payments.views import PaymentLinkDetailView, PaymentLinkView

urlpatterns = [
    path("", PaymentLinkView.as_view()),
    path("<str:slug>", PaymentLinkDetailView.as_view()),
]
