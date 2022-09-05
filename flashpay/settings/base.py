from datetime import timedelta
from pathlib import Path
from typing import Dict, Tuple, Union

import environ
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

BASE_DIR = Path(__file__).resolve().parent.parent

# Initialise environ class
# See https://django-environ.readthedocs.io
env = environ.Env()
env.read_env(BASE_DIR / ".env")


# ==============================================================================
# CORE SETTINGS
# ==============================================================================
DEBUG = env.bool("DEBUG", default=False)

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "corsheaders",
    "rest_framework",
    "cloudinary",
    "huey.contrib.djhuey",
]

LOCAL_APPS = ["flashpay.apps.core", "flashpay.apps.account", "flashpay.apps.payments"]

# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

WSGI_APPLICATION = "flashpay.wsgi.application"

ROOT_URLCONF = "flashpay.urls"

SITE_ID = 1


# ==============================================================================
# MIDDLEWARE SETTINGS
# ==============================================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==============================================================================
# TEMPLATES SETTINGS
# ==============================================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ==============================================================================
# DATABASES SETTINGS
# ==============================================================================
DATABASES = {
    "default": env.db("DATABASE_URL"),
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==============================================================================
# AUTHENTICATION AND AUTHORIZATION SETTINGS
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ==============================================================================
# I18N AND L10N SETTINGS
# ==============================================================================
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# ==============================================================================
# STATIC FILES SETTINGS
# ==============================================================================
STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR.parent.parent / "staticfiles"

STATICFILES_DIRS = [BASE_DIR / "static"]

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)


# ==============================================================================
# MEDIA FILES SETTINGS
# ==============================================================================
MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR.parent.parent / "media"


# ==============================================================================
# SECURITY
# ==============================================================================
SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_HTTPONLY = True

SECURE_BROWSER_XSS_FILTER = True

X_FRAME_OPTIONS = "DENY"


# ==============================================================================
# LOGGING
# ==============================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s " "%(process)d %(thread)d %(message)s"
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
}


# ==============================================================================
# THIRD-PARTY SETTINGS
# ==============================================================================
REST_FRAMEWORK: Dict[str, Union[str, Tuple[str], int]] = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticatedOrReadOnly",),
    "EXCEPTION_HANDLER": "flashpay.apps.core.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "flashpay.apps.core.paginators.CustomPageNumberPagination",
    "PAGE_SIZE": 5,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "flashpay.apps.account.authentication.CustomJWTAuthentication",
    ),
    "UNAUTHENTICATED_USER": "flashpay.apps.account.authentication.AnonymousUser",
}

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-requested-with",
    "x-public-key",
    "x-secret-key",
]

TESTNET_ALGOD_ADDRESS = env("TESTNET_ALGOD_ADDRESS")
TESTNET_ALGOD_CLIENT = AlgodClient("FP", TESTNET_ALGOD_ADDRESS, {"X-API-Key": "FP"})
TESTNET_INDEXER_ADDRESS = env("TESTNET_INDEXER_ADDRESS")
TESTNET_INDEXER_CLIENT = IndexerClient("FP", TESTNET_INDEXER_ADDRESS, {"X-API-Key": "FP"})

MAINNET_ALGOD_ADDRESS = env("MAINNET_ALGOD_ADDRESS")
MAINNET_ALGOD_CLIENT = AlgodClient("FP", MAINNET_ALGOD_ADDRESS, {"X-API-Key": "FP"})
MAINNET_INDEXER_ADDRESS = env("MAINNET_INDEXER_ADDRESS")
MAINNET_INDEXER_CLIENT = IndexerClient("FP", MAINNET_INDEXER_ADDRESS, {"X-API-Key": "FP"})

ENCRYPTION_KEY = env("ENCRYPTION_KEY")

SIMPLE_JWT = {
    "USER_ID_FIELD": "address",
    "USER_ID_CLAIM": "account_id",
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=1),
}

HUEY = {
    "name": "flashpay-core",
    "url": env("REDIS_URL"),
    "immediate_use_memory": False,
    "immediate": False,
    "consumer": {
        "workers": 4,
        "worker_type": "thread",
    },
}
FLASHPAY_MASTER_WALLET = "ZTFRJ36LCYELJMIHLK3CLXA7CAQX6T5T3DFWWXOAT462HXLBZCSUWJCXIY"
DEFAULT_PAYMENT_LINK_IMAGE = (
    "https://asset.cloudinary.com/flashpay/f6e11bc25a974729eb5fe362024e2c0d"
)
ASSETS_UPLOAD_API_KEY = env("ASSETS_UPLOAD_API_KEY")

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": env("CLOUDINARY_APP_NAME"),
    "API_KEY": env("CLOUDINARY_API_KEY"),
    "API_SECRET": env("CLOUDINARY_API_SECRET"),
}

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
