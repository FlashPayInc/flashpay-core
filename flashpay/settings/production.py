from .base import *  # noqa
from .base import env

# ==============================================================================
# CORE SETTINGS
# ==============================================================================
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("SECRET_KEY")

# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")


# ==============================================================================
# SECURITY
# ==============================================================================
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True

# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 * 52  # one year

# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = True

# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True

# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
# SECURE_HSTS_PRELOAD = True

# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = True


# ==============================================================================
# CACHING
# ==============================================================================
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env.str("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Mimicing memcache behavior.
            # https://github.com/jazzband/django-redis#memcached-exceptions-behavior
            "IGNORE_EXCEPTIONS": True,
        },
    }
}


# ==============================================================================
# SCOUT APM
# ==============================================================================
INSTALLED_APPS.insert(0, "scout_apm.django")  # noqa: F405

SCOUT_MONITOR = True

SCOUT_KEY = env.str("SCOUT_KEY")

SCOUT_NAME = env.str("SCOUT_NAME")

SCOUT_ERRORS_ENABLED = True


# ==============================================================================
# LOGGING
# ==============================================================================
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s " "%(process)d %(thread)d %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.db.backends": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        "scout_apm": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}


# ==============================================================================
# THIRD-PARTY SETTINGS
# ==============================================================================
# This is set to true to enable client sdk access the API
CORS_ALLOW_ALL_ORIGINS = True

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticatedOrReadOnly",),
    "EXCEPTION_HANDLER": "flashpay.apps.core.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "flashpay.apps.core.paginators.CustomPageNumberPagination",
    "PAGE_SIZE": 5,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "flashpay.apps.account.authentication.CustomJWTAuthentication",
    ),
    "UNAUTHENTICATED_USER": "flashpay.apps.account.authentication.AnonymousUser",
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
}

FLASHPAY_MASTER_WALLET = env("FLASHPAY_MASTER_WALLET")
