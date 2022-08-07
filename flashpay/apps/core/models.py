import uuid

from django.db import models


class Network(models.TextChoices):
    MAINNET = "mainnet"
    TESTNET = "testnet"


class BaseModel(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    network = models.CharField(max_length=20, choices=Network.choices, default=Network.MAINNET)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        abstract = True


class Asset(BaseModel):
    asa_id = models.IntegerField()
    short_name = models.CharField(max_length=20)
    long_name = models.CharField(max_length=100)
    image_url = models.URLField()
    decimals = models.PositiveIntegerField(default=1)

    def __str__(self) -> str:
        return self.long_name
