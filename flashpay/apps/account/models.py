from django.db import models

from flashpay.apps.core.models import BaseModel


class Account(BaseModel):

    address = models.CharField(max_length=58, unique=True)

    def __str__(self) -> str:
        return f"Account {self.address}"


class Setting(BaseModel):

    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="settings")
    email = models.EmailField(null=True)

    def __str__(self) -> str:
        return f"Settings For Account {self.account.address}"


class APIKey(BaseModel):

    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="api_keys")
    secret_key = models.CharField(max_length=100)
    public_key = models.CharField(max_length=100)


class Notification(BaseModel):

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    body = models.TextField()
    seen = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Notification {self.title}"
