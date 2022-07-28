import secrets
from typing import Iterable, Optional

from django.db import models
from django.utils import timezone

from flashpay.apps.core.models import BaseModel


class TransactionStatus(models.TextChoices):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class PaymentLink(BaseModel):

    asset = models.ForeignKey("core.Asset", on_delete=models.DO_NOTHING, null=True)
    account = models.ForeignKey("account.Account", on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    slug = models.CharField(max_length=50, unique=True, null=True)
    amount = models.DecimalField(max_digits=16, decimal_places=4, null=False, blank=False)
    image = models.ImageField(upload_to="payment-links", null=True)
    is_active = models.BooleanField(default=True)
    has_fixed_amount = models.BooleanField(default=False)
    is_one_time = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"PaymentLink {self.name}"

    def save(
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: Optional[str] = None,
        update_fields: Optional[Iterable[str]] = None,
    ) -> None:
        if not self.slug:
            self.slug = secrets.token_urlsafe(5)
        super().save(force_insert, force_update, using, update_fields)


class BaseTransaction(models.Model):

    txn_ref = models.CharField(max_length=20, unique=True)
    asset = models.ForeignKey("core.Asset", on_delete=models.DO_NOTHING, null=True)
    sender = models.CharField(max_length=58)
    recipient = models.CharField(max_length=58)
    txn_hash = models.TextField()
    amount = models.DecimalField(max_digits=16, decimal_places=4)
    status = models.CharField(
        max_length=50, choices=TransactionStatus.choices, default=TransactionStatus.PENDING
    )
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"Txn {self.txn_ref}"


class PaymentLinkTransaction(BaseTransaction):

    payment_link = models.ForeignKey(
        PaymentLink, on_delete=models.DO_NOTHING, null=True, related_name="transactions"
    )
