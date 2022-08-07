from algosdk.constants import ADDRESS_LEN

from django.db import models

from flashpay.apps.core.models import BaseModel


class Account(BaseModel):
    address = models.CharField(max_length=ADDRESS_LEN, unique=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Account {self.address}"


class Setting(BaseModel):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="settings")
    email = models.EmailField(null=True)

    def __str__(self) -> str:
        return f"Settings For Account {self.account.address}"


class APIKey(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="api_keys")
    secret_key = models.CharField(max_length=100)
    public_key = models.CharField(max_length=100)
