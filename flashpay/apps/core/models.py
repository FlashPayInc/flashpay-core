import uuid

from django.db import models


class Network(models.TextChoices):
    MAINNET = "mainnet"
    TESTNET = "testnet"


class BaseModel(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    network = models.CharField(max_length=20, choices=Network.choices, default=Network.TESTNET)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        abstract = True


class Asset(BaseModel):
    # For Algorand native token, `asa_id` is 0 for mainnet & 1 for testnet.
    asa_id = models.IntegerField(null=False, blank=False, unique=True)
    short_name = models.CharField(null=False, blank=False, max_length=20)
    long_name = models.CharField(null=False, blank=False, max_length=100)
    image_url = models.URLField(null=False, blank=False)
    decimals = models.PositiveIntegerField(default=1)

    def __str__(self) -> str:
        return self.long_name
