import secrets
import uuid
from decimal import Decimal
from typing import Iterable, Optional

from django.db import models
from django.db.models import Sum
from django.utils import timezone

from flashpay.apps.core.models import BaseModel


class TransactionStatus(models.TextChoices):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class TransactionType(models.TextChoices):
    PAYMENT_LINK = "payment_link"


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

    @property
    def total_revenue(self) -> Decimal:
        total: Optional[Decimal] = Transaction.objects.filter(
            txn_ref__icontains=self.uid.hex, status=TransactionStatus.SUCCESS
        ).aggregate(Sum("amount"))["amount__sum"]
        return total if total is not None else Decimal("0.0000")


class Transaction(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    txn_ref = models.CharField(max_length=42, unique=True)
    asset = models.ForeignKey("core.Asset", on_delete=models.DO_NOTHING, null=True)
    sender = models.CharField(max_length=58, null=True, blank=True)
    txn_type = models.CharField(
        max_length=50, choices=TransactionType.choices, default=TransactionType.PAYMENT_LINK
    )
    recipient = models.CharField(max_length=58)
    txn_hash = models.TextField(null=True, blank=True)
    amount = models.DecimalField(max_digits=16, decimal_places=4)
    status = models.CharField(
        max_length=50, choices=TransactionStatus.choices, default=TransactionStatus.PENDING
    )
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Txn {self.txn_ref}"
