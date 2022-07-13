from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/core/", include("flashpay.apps.core.urls")),
    path("api/accounts/", include("flashpay.apps.account.urls")),
]
handler404 = "flashpay.apps.core.views.handler_404"
handler500 = "flashpay.apps.core.views.handler_500"
