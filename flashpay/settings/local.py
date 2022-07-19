from .base import *  # noqa
from .base import env, timedelta

DEBUG = True

SECRET_KEY = env("SECRET_KEY", default="!!!SET DJANGO_SECRET_KEY!!!")

ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]


REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTStatelessUserAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "flashpay.apps.core.paginators.CustomCursorPagination",
    "PAGE_SIZE": 5,
}

SIMPLE_JWT = {
    "USER_ID_FIELD": "address",
    "USER_ID_CLAIM": "account_id",
    "ACCESS_TOKEN_LIFETIME": timedelta(days=4),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=10),
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}
