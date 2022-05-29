from .base import *  # noqa
from .base import env

DEBUG = True

SECRET_KEY = env("SECRET_KEY", default="!!!SET DJANGO_SECRET_KEY!!!")

ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}
