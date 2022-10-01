import secrets
import uuid
from decimal import Decimal
from typing import Iterable, Optional

from algosdk.constants import ADDRESS_LEN

from django.db import models
from django.db.models import QuerySet, Sum

from flashpay.apps.core.models import BaseModel, Network


class TransactionStatus(models.TextChoices):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class TransactionType(models.TextChoices):
    PAYMENT_LINK = "payment_link"
    NORMAL = "normal"


class PaymentLink(BaseModel):
    asset = models.ForeignKey(
        "core.Asset",
        to_field="asa_id",
        on_delete=models.PROTECT,
        null=False,
        blank=False,
    )
    account = models.ForeignKey(
        to="account.Account",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=False,
    )
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, null=False, blank=False)
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
            txn_reference__icontains=self.uid.hex, status=TransactionStatus.SUCCESS
        ).aggregate(Sum("amount"))["amount__sum"]
        return total if total is not None else Decimal("0.0000")

    def transactions(self) -> QuerySet:
        return Transaction.objects.filter(txn_reference__icontains=self.uid.hex)

    class Meta:
        ordering = ["-created_at"]


class Transaction(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, null=False, blank=False)
    txn_reference = models.CharField(max_length=42, unique=True, null=False, blank=False)
    asset = models.ForeignKey(
        "core.Asset",
        to_field="asa_id",
        on_delete=models.PROTECT,
        null=False,
    )
    sender = models.CharField(max_length=ADDRESS_LEN, null=False, blank=False)
    txn_type = models.CharField(
        max_length=50,
        choices=TransactionType.choices,
        default=TransactionType.PAYMENT_LINK,
        null=False,
        blank=False,
    )
    recipient = models.CharField(max_length=ADDRESS_LEN, null=False, blank=False)
    txn_hash = models.TextField(null=True, blank=True)
    amount = models.DecimalField(max_digits=16, decimal_places=4, null=False, blank=False)
    status = models.CharField(
        max_length=50, choices=TransactionStatus.choices, default=TransactionStatus.PENDING
    )
    network = models.CharField(max_length=20, choices=Network.choices, default=Network.TESTNET)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Transaction {self.txn_reference}"

    class Meta:
        ordering = ["-created_at"]


class DailyRevenue(BaseModel):
    account = models.ForeignKey(
        to="account.Account",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=False,
    )
    asset = models.ForeignKey(
        "core.Asset",
        on_delete=models.DO_NOTHING,
        null=False,
        blank=False,
    )
    amount = models.DecimalField(max_digits=16, decimal_places=4, null=False, blank=False)

    def __str__(self) -> str:
        return f"DailyRevenue for {self.account}"

    class Meta:
        ordering = ["created_at"]
