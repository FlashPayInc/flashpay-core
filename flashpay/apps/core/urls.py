from django.urls import path

from flashpay.apps.core.views import (
    AssetView,
    HealthCheckThirdPartyView,
    HealthCheckView,
    PingView,
)

urlpatterns = [
    path("/ping", PingView.as_view()),
    path("/health", HealthCheckView.as_view()),
    path("/assets", AssetView.as_view()),
    path("/health/thirdparty", HealthCheckThirdPartyView.as_view()),
]
