from django.urls import path

from flashpay.apps.core.views import PingView

urlpatterns = [
    path("ping", PingView.as_view()),
]
