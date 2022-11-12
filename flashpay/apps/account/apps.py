from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "flashpay.apps.account"

    def ready(self) -> None:
        import flashpay.apps.account.signals  # noqa: F401
