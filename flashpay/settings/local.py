from .base import *  # noqa
from .base import env

DEBUG = True

SECRET_KEY = env("SECRET_KEY", default="!!!SET DJANGO_SECRET_KEY!!!")

ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]


REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "EXCEPTION_HANDLER": "flashpay.apps.core.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "flashpay.apps.core.paginators.CustomCursorPagination",
    "PAGE_SIZE": 5,
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}
