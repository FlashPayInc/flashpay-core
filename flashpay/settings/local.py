from .base import *  # noqa
from .base import env, timedelta

DEBUG = True

SECRET_KEY = env("SECRET_KEY", default="!!!SET DJANGO_SECRET_KEY!!!")

ALLOWED_HOSTS = ["*"]

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
