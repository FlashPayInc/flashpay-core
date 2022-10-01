from algosdk.constants import ADDRESS_LEN

from django.db import models

from flashpay.apps.core.models import BaseModel


class Account(BaseModel):
    address = models.CharField(null=False, blank=False, max_length=ADDRESS_LEN, unique=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Account {self.address}"

    @property
    def is_authenticated(self) -> bool:
        return self.is_verified


class Setting(models.Model):
    account = models.OneToOneField(
        Account,
        related_name="settings",
        on_delete=models.CASCADE,
        null=False,
    )
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"<Settings For Account: {self.account.address}>"


class APIKey(BaseModel):
    # There can only be testnet and mainnet api keys for an account (i.e. two)
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, null=False, related_name="api_keys"
    )
    secret_key = models.CharField(null=False, blank=False, max_length=100)
    public_key = models.CharField(null=False, blank=False, max_length=100)

    class Meta:
        ordering = ["-created_at"]


class Webhook(BaseModel):
    # There can only be testnet and mainnet webhook urls for an account (i.e. two)
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, null=False, related_name="webhooks"
    )
    url = models.URLField(null=False, blank=False)

    class Meta:
        ordering = ["-created_at"]
