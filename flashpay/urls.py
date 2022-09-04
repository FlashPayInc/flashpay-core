from django.contrib import admin
from django.urls import include, path

from flashpay.apps.payments.views import TransactionsView, VerifyTransactionView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/core", include("flashpay.apps.core.urls")),
    path("api/payment-links", include("flashpay.apps.payments.urls")),
    path("api/accounts", include("flashpay.apps.account.urls")),
    path("api/transactions", TransactionsView.as_view()),
    path("api/transactions/verify/<str:txn_reference>", VerifyTransactionView.as_view()),
]
handler404 = "flashpay.apps.core.views.handler_404"
handler500 = "flashpay.apps.core.views.handler_500"
